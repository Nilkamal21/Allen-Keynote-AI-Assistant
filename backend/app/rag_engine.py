import os
import sys
import re
import json
import socket
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.config import COHERE_API_KEY
from backend.app.vector_store import HybridSearchEngine
from backend.app.reranker import Reranker

try:
    import cohere
    HAS_COHERE = True
except ImportError:
    HAS_COHERE = False

GENERIC_CATEGORY_HEADINGS = {
    "fever", "chill", "stomach", "head", "headache", "rectum", "stool", "urine",
    "skin", "eyes", "ears", "cough", "respiratory", "remedies", "index", "repertory",
    "bowel nosodes", "the bowel nosodes", "general", "constitution", "pain", "nausea",
    "nausea / vomiting", "belching / eructations", "fissure / piles"
}

SECTION_KEYWORDS = {
    "mental": ["Mental Generals", "Mental", "Mentals", "Mind"],
    "mind": ["Mental Generals", "Mental", "Mentals", "Mind"],
    "stomach": ["Stomach", "Gastro-intestinal System", "Digestive System", "Digestion", "NAUSEA / VOMITING"],
    "gastric": ["Stomach", "Gastro-intestinal System", "Digestive System"],
    "head": ["Head", "Outer Head", "HEADACHE"],
    "headache": ["Head", "Outer Head", "HEADACHE"],
    "fever": ["Fever"],
    "respiratory": ["Respiratory System", "Chest"],
    "cough": ["Respiratory System", "Chest"],
    "modalities": ["Modalities", "Motdalities"],
    "aggravation": ["Modalities"],
    "amelioration": ["Modalities"],
    "skin": ["Skin"],
    "sleep": ["Sleep"],
    "female": ["Female Reproductive System", "Female"],
    "male": ["Male Reproductive System", "Male"],
    "urinary": ["Urinary System", "Urinary", "Bladder", "Kidney", "Urine"],
}

def is_online() -> bool:
    try:
        socket.setdefaulttimeout(2.0)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("8.8.8.8", 53))
        sock.close()
        return True
    except Exception:
        return False

SYSTEM_PROMPT = """You are an expert AI clinical assistant for Allen's Keynotes.

GROUNDING RULES:
1. Answer the user's question concisely using ONLY the provided book passages below.
2. Provide a short, direct summary answer (max 3 sentences).
3. List ONLY the specific remedies and key symptoms requested by the user.
4. Include exact Allen's Keynotes Page Numbers.

BOOK PASSAGES:
{context_passages}

USER QUESTION: {query}
"""

class RAGEngine:
    def __init__(self, data_dir: str = "backend/data", cohere_api_key: str = None):
        self.cohere_api_key = cohere_api_key or COHERE_API_KEY
        self.search_engine = HybridSearchEngine(data_dir=data_dir)
        self.reranker = Reranker(api_key=self.cohere_api_key)
        self.cohere_client = None

        if HAS_COHERE and self.cohere_api_key:
            try:
                self.cohere_client = cohere.Client(self.cohere_api_key)
                print("[RAGEngine] Cohere LLM client initialized with .env API key.")
            except Exception as e:
                print(f"[RAGEngine] Cohere initialization error: {e}")

    def _detect_target_remedy(self, query: str) -> str:
        query_lower = query.lower()
        chunks = self.search_engine.chunks
        remedy_names = set(c["remedy_name"].lower() for c in chunks)
        
        for rname in sorted(list(remedy_names), key=lambda x: len(x), reverse=True):
            if rname in GENERIC_CATEGORY_HEADINGS:
                continue
            first_word = rname.split()[0]
            if len(first_word) >= 4 and first_word in query_lower:
                return rname
            if rname in query_lower:
                return rname
        return ""

    def _detect_target_sections(self, query: str) -> List[str]:
        query_lower = query.lower()
        matched_sections = []
        for kw, sec_list in SECTION_KEYWORDS.items():
            if kw in query_lower:
                matched_sections.extend(sec_list)
        return matched_sections

    def generate_answer(self, query: str, top_k_retrieve: int = 35, top_k_rerank: int = 6, force_offline: bool = False) -> Dict[str, Any]:
        """
        Smart RAG Engine:
        - Excludes generic index headings ('Fever', 'Stomach') from being rendered as remedy names.
        - Prioritizes real Materia Medica remedies (Aconite, Rhus Tox, Belladonna, Sulphur, etc.).
        """
        online_status = is_online() and not force_offline
        use_llm = online_status and (self.cohere_client is not None)

        target_remedy = self._detect_target_remedy(query)
        target_sections = self._detect_target_sections(query)

        # 1. Retrieve candidates
        candidates = self.search_engine.hybrid_search(query, top_k=top_k_retrieve)

        if not candidates:
            return {
                "query": query,
                "mode": "online" if use_llm else "offline",
                "ai_synthesis": "",
                "summary": "No relevant information could be found in Allen's Keynotes for your query.",
                "remedies": [],
                "disclaimer": "This information is retrieved directly from Allen's Keynotes for reference only."
            }

        # Filter out generic headings (like 'FEVER', 'STOMACH', 'HEADACHE') from remedy list
        valid_candidates = [c for c in candidates if c["remedy_name"].strip().lower() not in GENERIC_CATEGORY_HEADINGS]
        if not valid_candidates:
            valid_candidates = candidates

        # Prioritize main Materia Medica remedies (pages 20-421)
        materia_medica_candidates = [c for c in valid_candidates if c.get("section_type") == "materia_medica"]
        filtered_candidates = materia_medica_candidates if materia_medica_candidates else valid_candidates

        # Filter by Target Remedy if user named a specific remedy
        if target_remedy:
            remedy_matches = [c for c in valid_candidates if target_remedy in c["remedy_name"].lower()]
            if remedy_matches:
                filtered_candidates = remedy_matches

        # Filter by Target Section if user named a specific section
        if target_sections and not target_remedy:
            section_matches = [c for c in filtered_candidates if any(ts.lower() in c["section"].lower() for ts in target_sections)]
            if section_matches:
                filtered_candidates = section_matches

        # 2. Rerank filtered candidates
        top_passages = self.reranker.rerank(query, filtered_candidates, top_n=top_k_rerank)

        # 3. Build clean structured remedy cards
        remedies_map = {}
        context_str = ""

        for idx, p in enumerate(top_passages, 1):
            rem_name = p['remedy_name'].strip()
            if rem_name.lower() in GENERIC_CATEGORY_HEADINGS:
                continue

            rem_title = rem_name.title() if rem_name.isupper() else rem_name
            
            context_str += f"\n[Passage {idx}] Remedy: {rem_title} | Section: {p['section']} | Page: {p['start_page']}\n{p['text']}\n"

            if rem_title not in remedies_map:
                remedies_map[rem_title] = {
                    "remedy_name": rem_title,
                    "common_name": p.get('common_name', '').strip(),
                    "family": p.get('family', '').strip(),
                    "page_number": p['start_page'],
                    "sections": []
                }

            raw_lines = [l.strip() for l in p['text'].split('\n') if l.strip()]
            clean_symptoms = []
            for line in raw_lines:
                cleaned_line = re.sub(r'^[•\-\*\u25cf\u25a0\ufffd\s]+', '', line).strip()
                if cleaned_line and len(cleaned_line) > 3:
                    clean_symptoms.append(cleaned_line)

            if clean_symptoms:
                remedies_map[rem_title]["sections"].append({
                    "system_name": p['section'].strip(),
                    "page_number": p['start_page'],
                    "symptoms": clean_symptoms[:4]
                })

        structured_remedies = list(remedies_map.values())

        # Process LLM AI Synthesis if Online
        ai_synthesis = ""
        mode_label = "offline"

        if use_llm:
            try:
                full_prompt = SYSTEM_PROMPT.format(context_passages=context_str, query=query)
                res = self.cohere_client.chat(
                    message=full_prompt,
                    model="command-r-plus",
                    temperature=0.2
                )
                ai_synthesis = res.text.strip()
                mode_label = "online"
            except Exception as e:
                print(f"[RAGEngine] Cohere API call error: {e}. Falling back to offline mode.")
                mode_label = "offline"

        summary_text = f"According to Allen's Keynotes, relevant remedies for '{query}':"

        return {
            "query": query,
            "mode": mode_label,
            "ai_synthesis": ai_synthesis,
            "summary": summary_text,
            "remedies": structured_remedies,
            "disclaimer": "Information retrieved directly from Allen's Keynotes for educational and reference purposes only. Not intended for medical diagnosis or prescription."
        }

if __name__ == "__main__":
    rag = RAGEngine(data_dir="backend/data")
    test_q = "Which remedy is associated with fever and skin symptoms?"
    print(f"\nTesting Filtered RAG Engine for query: '{test_q}'\n")
    res = rag.generate_answer(test_q)
    print(f"Execution Mode: {res['mode'].upper()}")
    print("Summary:", res["summary"])
    if res["ai_synthesis"]:
        print("\n--- ONLINE COHERE CHAT AI SYNTHESIS ---")
        print(res["ai_synthesis"])
    print(f"\nExtracted {len(res['remedies'])} remedies cleanly:")
    for r in res["remedies"]:
        print(f"- {r['remedy_name']} (Page {r['page_number']})")

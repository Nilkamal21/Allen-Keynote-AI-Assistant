import os
import json
import re
import difflib
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import chromadb

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

COMMON_MEDICAL_WORDS = [
    "remedies", "remedy", "symptoms", "symptom", "headache", "stomach", "nausea",
    "vomiting", "fever", "pain", "burning", "aggravation", "amelioration", "cough",
    "diarrhea", "constipation", "chilling", "restlessness", "anxiety", "vertigo",
    "menses", "respiratory", "gastrointestinal", "cardiovascular", "urinary",
    "female", "male", "children", "pregnancy", "modalities", "relation"
]

ENGLISH_STOP_WORDS = {
    "what", "which", "where", "when", "who", "whom", "whose", "why", "how",
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "about",
    "against", "between", "into", "through", "during", "before", "after", "above", "below",
    "from", "up", "down", "out", "off", "over", "under", "again", "further", "then", "once",
    "can", "could", "shall", "should", "will", "would", "may", "might", "must",
    "this", "that", "these", "those", "patient", "person", "remedy", "remedies", "symptom", "symptoms",
    "mentioned", "associated", "according", "book", "say", "says", "show", "give", "list"
}

def tokenize_text(text: str) -> List[str]:
    tokens = re.findall(r'\b\w+\b', text.lower())
    return [t for t in tokens if len(t) > 1]

class HybridSearchEngine:
    def __init__(self, data_dir: str = "backend/data"):
        self.data_dir = data_dir
        self.chunks_path = os.path.join(data_dir, "processed_chunks.json")
        self.chroma_dir = os.path.join(data_dir, "chroma_db")
        
        self.chunks: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None
        self.embed_model = None
        self.chroma_client = None
        
        self.vocab_set = set(COMMON_MEDICAL_WORDS).union(ENGLISH_STOP_WORDS)
        self.vocab_list = list(COMMON_MEDICAL_WORDS)

        self._load_chunks()
        self._build_vocabulary()
        self._init_bm25()
        self._init_vector_db()

    def _load_chunks(self):
        if os.path.exists(self.chunks_path):
            with open(self.chunks_path, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)
            print(f"[HybridSearchEngine] Loaded {len(self.chunks)} chunks from {self.chunks_path}")
        else:
            print(f"[HybridSearchEngine] Warning: {self.chunks_path} not found.")

    def _build_vocabulary(self):
        for c in self.chunks:
            for w in tokenize_text(c["remedy_name"]):
                self.vocab_set.add(w)
            if c.get("common_name"):
                for w in tokenize_text(c["common_name"]):
                    self.vocab_set.add(w)
            for w in tokenize_text(c["section"]):
                self.vocab_set.add(w)
        self.vocab_list = sorted(list(self.vocab_set))

    def correct_typos(self, query: str) -> str:
        words = re.findall(r'\b\w+\b', query)
        if not words:
            return query

        corrected = []
        modified = False

        for w in words:
            w_lower = w.lower()
            if len(w_lower) <= 3 or w_lower in self.vocab_set or w_lower in ENGLISH_STOP_WORDS:
                corrected.append(w)
            else:
                matches = difflib.get_close_matches(w_lower, self.vocab_list, n=1, cutoff=0.78)
                if matches:
                    corrected.append(matches[0])
                    modified = True
                else:
                    corrected.append(w)

        corrected_query = " ".join(corrected)
        if modified:
            print(f"[HybridSearchEngine] Typo Auto-Corrected: '{query}' -> '{corrected_query}'")
        return corrected_query

    def _init_bm25(self):
        if not self.chunks:
            return
        corpus = []
        for c in self.chunks:
            doc_str = f"{c['remedy_name']} {c['common_name']} {c['section']} {c['text']} {' '.join(c['cross_references'])}"
            corpus.append(tokenize_text(doc_str))
        
        self.bm25 = BM25Okapi(corpus)
        print(f"[HybridSearchEngine] BM25 Index built with {len(corpus)} documents.")

    def _init_vector_db(self):
        os.makedirs(self.chroma_dir, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_dir)

        if HAS_SENTENCE_TRANSFORMERS:
            try:
                print("[HybridSearchEngine] Loading SentenceTransformer 'all-MiniLM-L6-v2'...")
                self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                print(f"[HybridSearchEngine] Error loading SentenceTransformer: {e}")
                self.embed_model = None
        
        self.collection = self.chroma_client.get_or_create_collection(
            name="allens_keynotes",
            metadata={"hnsw:space": "cosine"}
        )

    def index_vector_db(self, force_reindex: bool = False):
        if not self.chunks:
            return

        current_count = self.collection.count()
        if current_count >= len(self.chunks) and not force_reindex:
            print(f"[HybridSearchEngine] Vector DB already indexed with {current_count} items.")
            return

        print(f"[HybridSearchEngine] Indexing {len(self.chunks)} chunks into ChromaDB...")
        
        batch_size = 256
        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for i, c in enumerate(self.chunks):
            doc_str = f"Remedy: {c['remedy_name']}\nSection: {c['section']}\nSymptoms: {c['text']}"
            ids.append(c["chunk_id"])
            documents.append(doc_str)
            metadatas.append({
                "remedy_name": c["remedy_name"],
                "common_name": c.get("common_name", ""),
                "section": c["section"],
                "page_number": c["start_page"],
                "section_type": c["section_type"]
            })

            if self.embed_model:
                emb = self.embed_model.encode(doc_str).tolist()
                embeddings.append(emb)

            if len(ids) >= batch_size or i == len(self.chunks) - 1:
                if self.embed_model and embeddings:
                    self.collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
                else:
                    self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
                ids, documents, metadatas, embeddings = [], [], [], []

        print(f"[HybridSearchEngine] Successfully indexed {self.collection.count()} chunks into ChromaDB.")

    def search_bm25(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        if not self.bm25 or not self.chunks:
            return []
        
        tokens = tokenize_text(query)
        if not tokens:
            return []
        
        scores = self.bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for rank, idx in enumerate(top_indices):
            if scores[idx] > 0:
                chunk = self.chunks[idx].copy()
                chunk["bm25_score"] = float(scores[idx])
                chunk["bm25_rank"] = rank + 1
                results.append(chunk)
        return results

    def search_vector(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        if not self.collection or self.collection.count() == 0:
            return []
        
        if self.embed_model:
            query_emb = self.embed_model.encode(query).tolist()
            res = self.collection.query(query_embeddings=[query_emb], n_results=top_k)
        else:
            res = self.collection.query(query_texts=[query], n_results=top_k)

        results = []
        if res and res["ids"] and len(res["ids"][0]) > 0:
            found_ids = res["ids"][0]
            distances = res["distances"][0] if "distances" in res and res["distances"] else [0]*len(found_ids)
            
            chunk_map = {c["chunk_id"]: c for c in self.chunks}
            for rank, (cid, dist) in enumerate(zip(found_ids, distances)):
                if cid in chunk_map:
                    chunk = chunk_map[cid].copy()
                    chunk["vector_distance"] = float(dist)
                    chunk["vector_rank"] = rank + 1
                    results.append(chunk)
        return results

    def hybrid_search(self, raw_query: str, top_k: int = 10, bm25_weight: float = 0.5, vector_weight: float = 0.5) -> List[Dict[str, Any]]:
        query = self.correct_typos(raw_query)

        bm25_results = self.search_bm25(query, top_k=30)
        vector_results = self.search_vector(query, top_k=30)

        rrf_scores = {}
        chunk_map = {}

        for c in bm25_results:
            cid = c["chunk_id"]
            rank = c["bm25_rank"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + bm25_weight * (1.0 / (60.0 + rank))
            chunk_map[cid] = c

        for c in vector_results:
            cid = c["chunk_id"]
            rank = c["vector_rank"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + vector_weight * (1.0 / (60.0 + rank))
            if cid not in chunk_map:
                chunk_map[cid] = c

        query_clean = query.strip().lower()
        for cid, c in chunk_map.items():
            remedy_lower = c["remedy_name"].lower()
            if query_clean in remedy_lower or remedy_lower in query_clean:
                rrf_scores[cid] += 0.05

        sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]

        final_results = []
        for cid in sorted_ids:
            chunk = chunk_map[cid].copy()
            chunk["rrf_score"] = float(rrf_scores[cid])
            final_results.append(chunk)

        return final_results

if __name__ == "__main__":
    searcher = HybridSearchEngine(data_dir="backend/data")
    
    test_queries = [
        "What remedies are mentioned for respiratory symptoms?",
        "Nux Vomca remeies for stomach pain"
    ]

    for q in test_queries:
        print(f"\nRaw Query: '{q}'")
        res = searcher.hybrid_search(q, top_k=2)
        for i, r in enumerate(res):
            print(f"  [{i+1}] {r['remedy_name']} ({r['section']}) — Page {r['start_page']}")

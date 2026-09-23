import os
import sys
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.app.config import COHERE_API_KEY

try:
    import cohere
    HAS_COHERE = True
except ImportError:
    HAS_COHERE = False

class Reranker:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or COHERE_API_KEY
        self.cohere_client = None
        if HAS_COHERE and self.api_key:
            try:
                self.cohere_client = cohere.Client(self.api_key)
                print("[Reranker] Cohere Reranker initialized successfully.")
            except Exception as e:
                print(f"[Reranker] Cohere initialization failed: {e}")
                self.cohere_client = None
        else:
            print("[Reranker] Running in fallback mode (RRF Hybrid Rank).")

    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_n: int = 8) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        if self.cohere_client:
            try:
                doc_texts = [f"Remedy: {c['remedy_name']}\nSection: {c['section']}\nSymptoms: {c['text']}" for c in chunks]
                response = self.cohere_client.rerank(
                    model="rerank-english-v3.0",
                    query=query,
                    documents=doc_texts,
                    top_n=min(top_n, len(chunks))
                )
                
                reranked_results = []
                for hit in response.results:
                    idx = hit.index
                    chunk = chunks[idx].copy()
                    chunk["rerank_score"] = float(hit.relevance_score)
                    reranked_results.append(chunk)
                print(f"[Reranker] Cohere Rerank successfully ranked top {len(reranked_results)} passages.")
                return reranked_results
            except Exception as e:
                print(f"[Reranker] Cohere Rerank call error: {e}. Falling back to RRF rankings.")

        return chunks[:top_n]

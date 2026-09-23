import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.config import COHERE_API_KEY
from backend.app.vector_store import HybridSearchEngine
from backend.app.rag_engine import RAGEngine
from backend.app.main import app

client = TestClient(app)

def test_env_loading():
    """Verify .env file is loaded and COHERE_API_KEY is present."""
    assert COHERE_API_KEY != "", "COHERE_API_KEY should not be empty."
    assert COHERE_API_KEY.startswith("cohere_"), "COHERE_API_KEY should be a valid Cohere key string."

def test_typo_correction():
    """Verify fuzzy spell correction handles typos correctly."""
    searcher = HybridSearchEngine(data_dir="backend/data")
    corrected = searcher.correct_typos("Nux Vomca remeies for stomach pain")
    assert "nux" in corrected.lower()
    assert "vomica" in corrected.lower()
    assert "remedies" in corrected.lower()

def test_rag_online_mode():
    """Verify Online RAG mode using Cohere LLM API."""
    rag = RAGEngine(data_dir="backend/data")
    query = "Which remedies are associated with burning stomach pain?"
    res = rag.generate_answer(query, force_offline=False)
    
    assert res["query"] == query
    assert res["mode"] in ["online", "offline"]
    assert len(res["remedies"]) > 0, "Should retrieve matching remedies from Allen's Keynotes."
    assert "page_number" in res["remedies"][0], "Remedies must include exact page numbers."
    if res["mode"] == "online":
        assert len(res["ai_synthesis"]) > 0, "Online mode should generate AI clinical synthesis."

def test_rag_offline_mode():
    """Verify Offline RAG fallback mode (simulating offline / forced local mode)."""
    rag = RAGEngine(data_dir="backend/data")
    query = "What symptoms are mentioned under Nux Vomica?"
    res = rag.generate_answer(query, force_offline=True)
    
    assert res["mode"] == "offline"
    assert len(res["remedies"]) > 0, "Offline mode must retrieve remedy cards."
    assert res["remedies"][0]["remedy_name"].lower() == "nux vomica"

def test_api_health_endpoint():
    """Verify FastAPI /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["indexed_chunks"] > 0

def test_api_chat_endpoint():
    """Verify POST /api/chat endpoint."""
    response = client.post(
        "/api/chat",
        json={"query": "Headache worse in sunlight"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "remedies" in data
    assert len(data["remedies"]) > 0

def test_api_remedies_directory_endpoint():
    """Verify GET /api/remedies endpoint."""
    response = client.get("/api/remedies")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 200, "Allen's Keynotes contains over 200 remedies."

def test_api_remedy_details_endpoint():
    """Verify GET /api/remedy/Bryonia endpoint."""
    response = client.get("/api/remedy/Bryonia")
    assert response.status_code == 200
    data = response.json()
    assert "bryonia" in data["remedy_name"].lower()
    assert len(data["sections"]) > 0

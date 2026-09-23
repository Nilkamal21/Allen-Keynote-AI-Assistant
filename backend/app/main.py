import os
import sys
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.rag_engine import RAGEngine

app = FastAPI(
    title="Allen's Keynotes AI Assistant API",
    description="Grounded AI Assistant and RAG Search Engine for Allen's Keynotes Homeopathic Reference Book.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_dir = os.path.join(os.path.dirname(__file__), "../data")
frontend_dir = os.path.join(os.path.dirname(__file__), "../../frontend")

rag_engine = RAGEngine(data_dir=data_dir)

class QueryRequest(BaseModel):
    query: str

class SectionItem(BaseModel):
    system_name: str
    page_number: int
    symptoms: List[str]

class RemedyItem(BaseModel):
    remedy_name: str
    common_name: Optional[str] = ""
    family: Optional[str] = ""
    page_number: int
    sections: List[SectionItem]

class QueryResponse(BaseModel):
    query: str
    mode: str
    ai_synthesis: Optional[str] = ""
    summary: str
    remedies: List[RemedyItem]
    disclaimer: str

@app.get("/")
def serve_frontend():
    index_file = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Allen's Keynotes AI Assistant API is running.", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "ok", "indexed_chunks": len(rag_engine.search_engine.chunks)}

@app.post("/api/chat", response_model=QueryResponse)
def chat_endpoint(request: QueryRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    response = rag_engine.generate_answer(query)
    return response

@app.get("/api/remedies")
def list_remedies():
    chunks = rag_engine.search_engine.chunks
    remedy_map = {}
    for c in chunks:
        name = c["remedy_name"]
        if name not in remedy_map:
            remedy_map[name] = {
                "remedy_name": name,
                "common_name": c.get("common_name", ""),
                "family": c.get("family", ""),
                "start_page": c["start_page"],
                "section_type": c["section_type"]
            }
    return {"total": len(remedy_map), "remedies": list(remedy_map.values())}

@app.get("/api/remedy/{remedy_name}")
def get_remedy_details(remedy_name: str):
    chunks = rag_engine.search_engine.chunks
    matches = [c for c in chunks if c["remedy_name"].lower() == remedy_name.lower()]
    if not matches:
        matches = [c for c in chunks if remedy_name.lower() in c["remedy_name"].lower()]
    
    if not matches:
        raise HTTPException(status_code=404, detail=f"Remedy '{remedy_name}' not found.")
    
    return {
        "remedy_name": matches[0]["remedy_name"],
        "common_name": matches[0].get("common_name", ""),
        "family": matches[0].get("family", ""),
        "total_sections": len(matches),
        "sections": [
            {
                "section": m["section"],
                "page_number": m["start_page"],
                "text": m["text"],
                "cross_references": m.get("cross_references", [])
            } for m in matches
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000)

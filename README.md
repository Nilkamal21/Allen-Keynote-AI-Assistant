# 🌿 Allen's Keynotes AI Assistant

> **A Grounded AI Assistant and Structure-Aware RAG Engine for *Allen's Keynotes*, a Classic Homeopathic Reference Book (552 Pages).**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-emerald.svg)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorDB-purple.svg)](https://www.trychroma.com/)
[![React Native Ready](https://img.shields.io/badge/React%20Native-Supported-cyan.svg)](https://reactnative.dev/)
[![Tests Passed](https://img.shields.io/badge/Pytest-8%2F8%20PASSED-brightgreen.svg)](https://docs.pytest.org/)

Built specifically for medical practitioners, students, and homeopathy professionals to query **Allen's Keynotes** using natural language without technical complexity or hallucinated medical advice.

---

## 🚀 Deployment Status: **READY FOR PRODUCTION**

* ✅ **PDF Ingestion:** 2,019 structure-aware remedy/section chunks parsed with page numbers.
* ✅ **Hybrid Search Engine:** BM25 Exact Match + ChromaDB Vector Search + Reciprocal Rank Fusion (RRF).
* ✅ **Dual Online/Offline Mode:** Uses Cohere LLM (`command-r-plus`) when online; falls back to local CPU structured mode when offline or rate-limited.
* ✅ **Typo Protection:** Fuzzy spell-corrector with stop-word protection (`Nux Vomca` $\rightarrow$ `Nux Vomica`).
* ✅ **React Native Ready:** Complete mobile component (`mobile/AllenKeynotesScreen.jsx`).
* ✅ **Automated Test Suite:** 8/8 `pytest` test cases passing.

---

## 🛠 System Architecture

```text
               Allen's Keynotes PDF (552 Pages)
                              │
                    PyMuPDF Struct-Parser
                              │
                    2,019 Structured Chunks
                  (Remedy, Section, Page #)
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
         BM25 Search                    ChromaDB Vector
   (Exact term matching)             (Semantic similarity)
             │                                 │
             └────────────────┬────────────────┘
                              ▼
                     Reciprocal Rank Fusion (RRF)
                              │
                      Cohere Reranker (v3.0)
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
        🟢 Online Mode               ⚡ Offline Mode
    (Cohere Chat Synthesis)       (Local Direct Extraction)
               │                             │
               └──────────────┬──────────────┘
                              ▼
                Clean Mobile & Web Remedy Cards
```

---

## ✨ Features

1. **Strict Answer Grounding:** Answers are derived exclusively from *Allen's Keynotes*.
2. **Exact Page References:** Cites exact remedy names, sections, and PDF page numbers (`Allen's Keynotes — Page X`).
3. **Intent-Aware Query Filtering:**
   * Querying a specific remedy (e.g. *"What are the mental symptoms of Aconitum?"*) filters output to **only Aconitum** and **only Mental Generals**.
   * Broad queries (e.g. *"What remedies are mentioned for respiratory symptoms?"*) return specific remedy cards (*Psorinum*, *Hepar Sulphur*, *Pulsatilla*).
4. **Fuzzy Typo Correction:** Auto-corrects misspelled terms (`sympoms` $\rightarrow$ `symptoms`) while protecting English question words (`What`, `Which`).
5. **Zero-Cost / ₹0 Local CPU Execution:** Works 100% offline without mandatory paid API subscriptions.

---

## 📁 Repository Structure

```text
Allen Keynote/
├── backend/
│   ├── app/
│   │   ├── config.py           # Auto-loads .env variables
│   │   ├── parser.py           # Structure-aware PDF extraction engine
│   │   ├── vector_store.py     # BM25 + ChromaDB + RRF Hybrid Search + Typo Corrector
│   │   ├── reranker.py         # Cohere Reranker module with fallback
│   │   ├── rag_engine.py       # Grounded RAG engine (Online Chat / Offline Fallback)
│   │   └── main.py             # FastAPI REST server & static web handler
│   └── data/
│       ├── processed_chunks.json # Structured book dataset (2,019 chunks)
│       └── chroma_db/            # Vector store index
├── frontend/
│   └── index.html              # Glassmorphic web UI
├── mobile/
│   └── AllenKeynotesScreen.jsx # Drop-in React Native screen component
├── tests/
│   └── test_allens_keynotes.py # Pytest test suite (8/8 tests)
├── .env                        # Environment configuration (Cohere API key)
├── .gitignore                  # Git exclusion rules
├── requirements.txt            # Python dependencies
├── run_app.py                  # One-line app launcher
└── README.md                   # Documentation
```

---

## ⚙️ Installation & Setup

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-username/allens-keynotes-ai.git
cd "Allen Keynote"
pip install -r requirements.txt
```

### 2. Configure Environment Variables (Optional)
Create a `.env` file in the project root:
```env
COHERE_API_KEY=your_cohere_api_key_here
```
*(Note: If no API key is provided, the system seamlessly operates in 100% Local Offline Mode).*

---

## 🚀 Running the Application

Start the server:
```bash
python run_app.py
```

Open your browser at: **`http://127.0.0.1:8000`**

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the Web Frontend Interface |
| `GET` | `/health` | Server health check and index count |
| `POST` | `/api/chat` | Main RAG query endpoint (accepts `{"query": "..."}`) |
| `GET` | `/api/remedies` | Directory of all ~240 remedies in *Allen's Keynotes* |
| `GET` | `/api/remedy/{name}` | Structured sections and symptoms for a specific remedy |

---

## 📱 Mobile App (React Native)

To integrate into a React Native / Expo application:

1. Copy [`mobile/AllenKeynotesScreen.jsx`](file:///C:/Users/adhik/OneDrive/Desktop/Allen%20Keynote/mobile/AllenKeynotesScreen.jsx) into your mobile app project.
2. Set `API_BASE_URL` to your backend server URL or local IP (e.g. `http://192.168.1.100:8000`).
3. Import and render the component in your mobile app navigator.

---

## 🧪 Running Automated Tests

Run the full `pytest` test suite:
```bash
pytest tests/test_allens_keynotes.py -v
```

---

## ⚠️ Medical Disclaimer

*Information retrieved directly from Allen's Keynotes for educational and reference purposes only. Not intended for medical diagnosis, clinical prescription, or replacing professional healthcare advice.*

# AI-Powered Financial Chatbot

## Overview
MVP providing:
- Chatbot (Streamlit UI)
- Admin portal (Streamlit + backend endpoints)
- RAG pipeline (FAISS + SentenceTransformers)
- Mock bank APIs
- SQLite data persistence

## Quickstart
1. Create venv & install:
   python -m venv venv && source venv/bin/activate
   pip install -r backend/requirements.txt

2. Run backend:
   uvicorn backend.app.main:app --reload --port 8000

3. Ingest docs:
   python ingestion/ingest_docs.py "Business case - Data Scientist.docx"

4. Run frontend:
   streamlit run frontend/streamlit_app.py

## Default users:
- admin/adminpass (role=admin)
- alice/alice123 (role=customer)


# ingestion/ingest_docs.py
import argparse
from docx import Document
from backend.app.rag_store import RAGStore

def read_docx(path):
    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return paragraphs

def ingest(path, source_name=None):
    source = source_name or path
    texts = []
    if path.lower().endswith(".docx"):
        texts = read_docx(path)
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            texts = [l.strip() for l in f.readlines() if l.strip()]
    docs = []
    for t in texts:
        dtype = "rule" if "limit" in t.lower() or "daily" in t.lower() else "sanction" if "blacklist" in t.lower() or "sanction" in t.lower() else "rule"
        docs.append({"text": t, "source": source, "type": dtype})
    rag = RAGStore()
    rag.add_documents(docs)
    print(f"Added {len(docs)} docs from {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    ingest(args.path)

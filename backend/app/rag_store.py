from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import pickle
from typing import List, Dict

class RAGStore:
    def __init__(self, index_path="faiss.index", meta_path="faiss_meta.pkl", embed_model_name="all-MiniLM-L6-v2"):
        self.index_path = index_path
        self.meta_path = meta_path
        self.model = SentenceTransformer(embed_model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

        self.index = None
        self.metadatas = []

        self._load_or_create()

    # -------------------------------------------------
    # Safe loader with auto–repair
    # -------------------------------------------------
    def _load_or_create(self):
        index_exists = os.path.exists(self.index_path)
        meta_exists = os.path.exists(self.meta_path)

        if index_exists and meta_exists:
            # Load index + metadata
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "rb") as f:
                self.metadatas = pickle.load(f)

            # -------------------------------------------------
            # FIX: repair mismatch
            # -------------------------------------------------
            index_size = self.index.ntotal
            meta_size = len(self.metadatas)

            if index_size != meta_size:
                print("⚠️ WARNING: FAISS index size and metadata size mismatch detected!")
                print(f"   index vectors = {index_size}, metadata items = {meta_size}")
                print("   Auto-fixing...")

                keep = min(index_size, meta_size)

                # Trim metadata
                self.metadatas = self.metadatas[:keep]

                # Trim index vectors by reconstructing
                if keep > 0:
                    vectors = np.vstack([self.index.reconstruct(i) for i in range(keep)])
                    new_index = faiss.IndexFlatL2(self.dim)
                    new_index.add(vectors)
                    self.index = new_index
                else:
                    # Reset to empty
                    self.index = faiss.IndexFlatL2(self.dim)
                    self.metadatas = []

                self.save()

        else:
            # brand new index
            self.index = faiss.IndexFlatL2(self.dim)
            self.metadatas = []
            self.save()

    # -------------------------------------------------
    # Save files
    # -------------------------------------------------
    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadatas, f)

    # -------------------------------------------------
    # Add documents safely
    # -------------------------------------------------
    def add_documents(self, docs: List[Dict]):
        texts = [d["text"] for d in docs]
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

        # add vectors
        self.index.add(embeddings)

        # add metadata
        for d in docs:
            self.metadatas.append({
                "text": d.get("text"),
                "type": d.get("type", "rule"),
                "source": d.get("source", "dynamic"),
                "meta": d.get("meta", {})
            })

        self.save()

    # -------------------------------------------------
    # Query (safe)
    # -------------------------------------------------
    def query(self, query_text: str, top_k: int = 5):
        if self.index.ntotal == 0:
            return []

        q_emb = self.model.encode([query_text], convert_to_numpy=True)
        D, I = self.index.search(q_emb, top_k)

        results = []
        for idx in I[0]:
            if 0 <= idx < len(self.metadatas):
                results.append(self.metadatas[idx])

        return results

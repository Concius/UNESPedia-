# vector_stores/faiss_store.py

import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from .base import VectorStore   # delete if no ABC

class FAISSStore(VectorStore):
    def __init__(self, path: str, embedding_model: str, device: str = "cpu"):
        self.path = path
        self.encoder = SentenceTransformer(embedding_model, device=device)
        self.dim = self.encoder.get_sentence_embedding_dimension()
        self.index = None
        self.texts = []
        self.metadatas = []
        if os.path.exists(path):
            self._load()

    # ---------- persistence ----------
    def _save(self):
        with open(self.path, "wb") as f:
            pickle.dump({"index": faiss.serialize_index(self.index),
                         "texts": self.texts,
                         "metadatas": self.metadatas}, f)

    def _load(self):
        with open(self.path, "rb") as f:
            data = pickle.load(f)
            self.index = faiss.deserialize_index(data["index"])
            self.texts = data["texts"]
            self.metadatas = data["metadatas"]

    def carregar_ou_criar(self, chunks=None, metadados=None):
        """ABC hook: load or create index."""
        if chunks:                # creation path
            self.adicionar(chunks, metadados)
        # else: pure load path already handled in __init__

    # ---------- CRUD ----------
    def adicionar(self, chunks, metadados=None):
        if not chunks:
            return
        embs = self.encoder.encode(chunks, normalize_embeddings=True)
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.dim)  # cosine similarity
        self.index.add(np.array(embs, dtype=np.float32))
        self.texts.extend(chunks)
        self.metadatas.extend(metadados or [{} for _ in chunks])
        self._save()

    def buscar(self, query_texts, n_results=5, where=None):
        assert self.index is not None, "Índice vazio."
        emb = self.encoder.encode([query_texts], normalize_embeddings=True)
        D, I = self.index.search(np.array(emb, dtype=np.float32), k=n_results)
        docs, meta = [], []
        for idx in I[0]:
            if idx != -1:
                docs.append(self.texts[idx])
                meta.append(self.metadatas[idx])
        # crude post-filter if where clause given
        if where and 'fonte' in where:
            docs = [d for d, m in zip(docs, meta) if m.get('fonte') == where['fonte']]
            meta = [m for m in meta if m.get('fonte') == where['fonte']]
        return {"documents": [docs], "metadatas": [meta]}
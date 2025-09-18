# vector_stores/chroma_store.py

import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
from .base import VectorStore

class ChromaDBStore(VectorStore):
    def __init__(self, path: str, collection_name: str, embedding_model: str, device: str = "cpu"):
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model, device=device
        )
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef
        )

    def carregar_ou_criar(self, chunks=None, metadados=None):
        """ABC hook: load or create index."""
        if chunks:                # creation path
            self.adicionar(chunks, metadados)
        # else: pure load path already handled in __init__
    # ---------- CRUD ----------
    def adicionar(self, chunks, metadados=None):
        if not chunks:
            return
        count = self.collection.count()
        ids = [f"chunk_{count + i}" for i in range(len(chunks))]
        self.collection.add(documents=chunks, metadatas=metadados, ids=ids)

    def buscar(self, query_texts, n_results=5, where=None):
        return self.collection.query(
            query_texts=[query_texts],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas"]
        )
# vector_stores/chroma_store.py

import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
from .base import VectorStore

class ChromaDBStore(VectorStore):
    def __init__(self, path, collection_name):
        self.path = path
        self.collection_name = collection_name
        self.cliente = chromadb.PersistentClient(path=self.path)
        self.colecao = self._carregar_colecao()

    def _carregar_colecao(self):
        """Carrega ou cria a coleção no ChromaDB."""
        default_ef = embedding_functions.DefaultEmbeddingFunction()
        return self.cliente.get_or_create_collection(
            name=self.collection_name,
            embedding_function=default_ef
        )

    def carregar_ou_criar(self, chunks, metadados):
        """No ChromaDB, get_or_create_collection já faz isso. Apenas adicionamos se houver chunks."""
        if chunks:
            self.adicionar(chunks, metadados)

    def adicionar(self, chunks, metadados):
        """Adiciona documentos à coleção."""
        if not chunks:
            return
        
        # Gera IDs únicos para os novos chunks
        # Para evitar colisões, podemos basear os IDs no número de documentos já existentes
        count = self.colecao.count()
        ids = [f"chunk_{count + i}" for i in range(len(chunks))]
        
        try:
            self.colecao.add(documents=chunks, metadatas=metadados, ids=ids)
            st.success(f"{len(chunks)} novos chunks adicionados ao ChromaDB!")
        except Exception as e:
            st.error(f"Erro ao adicionar chunks ao ChromaDB: {e}")

    def buscar(self, query_texts, n_results, where=None):
        """Busca documentos na coleção."""
        try:
            return self.colecao.query(
                query_texts=[query_texts],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas"]
            )
        except Exception as e:
            st.error(f"Erro ao buscar no ChromaDB: {e}")
            return None
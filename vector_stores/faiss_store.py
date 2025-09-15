# vector_stores/faiss_store.py

import streamlit as st
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from .base import VectorStore

class FAISSStore(VectorStore):
    def __init__(self, path):
        self.path = path
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.documents = []  # Lista para guardar os textos e metadados
        self._carregar_indice_e_documentos()

    def _carregar_indice_e_documentos(self):
        """Carrega o índice FAISS e a lista de documentos do disco."""
        try:
            with open(self.path, "rb") as f:
                data = pickle.load(f)
                self.index = faiss.deserialize_index(data["index"])
                self.documents = data["documents"]
                st.info(f"Índice FAISS carregado com {len(self.documents)} documentos.")
        except FileNotFoundError:
            # Se o ficheiro não existe, criamos um índice vazio
            embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatL2(embedding_dim)
            st.info("Nenhum índice FAISS encontrado. Um novo foi criado.")
        except Exception as e:
            st.error(f"Erro ao carregar o índice FAISS: {e}")

    def _salvar_indice_e_documentos(self):
        """Salva o índice FAISS e a lista de documentos no disco."""
        try:
            with open(self.path, "wb") as f:
                index_serializado = faiss.serialize_index(self.index)
                data = {"index": index_serializado, "documents": self.documents}
                pickle.dump(data, f)
        except Exception as e:
            st.error(f"Erro ao salvar o índice FAISS: {e}")

    def carregar_ou_criar(self, chunks, metadados):
        """Se não houver chunks, o carregamento já foi feito. Se houver, adiciona-os."""
        if chunks:
            self.adicionar(chunks, metadados)

    def adicionar(self, chunks, metadados):
        """Adiciona documentos ao índice FAISS."""
        if not chunks:
            return
        
        try:
            # Gera embeddings para os novos chunks
            embeddings = self.embedding_model.encode(chunks, convert_to_tensor=False)
            
            # Adiciona os embeddings ao índice FAISS
            self.index.add(np.array(embeddings).astype('float32'))
            
            # Adiciona os textos e metadados à nossa lista de documentos
            for i in range(len(chunks)):
                self.documents.append({"document": chunks[i], "metadata": metadados[i]})
            
            # Salva as alterações no disco
            self._salvar_indice_e_documentos()
            st.success(f"{len(chunks)} novos chunks adicionados ao FAISS!")
            
        except Exception as e:
            st.error(f"Erro ao adicionar chunks ao FAISS: {e}")

    def buscar(self, query_texts, n_results, where=None):
        """Busca documentos no índice FAISS."""
        try:
            query_embedding = self.embedding_model.encode([query_texts])
            distances, indices = self.index.search(np.array(query_embedding).astype('float32'), n_results)
            
            # Formata a saída para ser compatível com o que o ChromaDB retorna
            docs_encontrados = []
            metadados_encontrados = []
            
            # O 'where' no FAISS é um pós-filtro manual
            resultados_filtrados_indices = []
            if where and 'fonte' in where:
                for idx in indices[0]:
                    if self.documents[idx]['metadata']['fonte'] == where['fonte']:
                        resultados_filtrados_indices.append(idx)
            else:
                resultados_filtrados_indices = indices[0]

            for idx in resultados_filtrados_indices:
                if idx != -1: # FAISS retorna -1 se não encontrar vizinhos suficientes
                    docs_encontrados.append(self.documents[idx]['document'])
                    metadados_encontrados.append(self.documents[idx]['metadata'])
            
            return {"documents": [docs_encontrados], "metadatas": [metadados_encontrados]}
        except Exception as e:
            st.error(f"Erro ao buscar no FAISS: {e}")
            return None
# vector_store_factory.py

from vector_stores.chroma_store import ChromaDBStore
from vector_stores.faiss_store import FAISSStore

def get_vector_store(config):
    """
    Retorna uma instância do Vector Store apropriado com base na configuração.
    """
    store_type = config.get('type')
    
    if store_type == "chroma":
        return ChromaDBStore(
            path=config.get('path'),
            collection_name=config.get('collection_name')
        )
    # MODIFICADO: Adiciona a lógica para criar um FAISSStore
    elif store_type == "faiss":
        return FAISSStore(path=config.get('path'))
        
    else:
        raise ValueError(f"Vector Store desconhecido: {store_type}")
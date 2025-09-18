# vector_store_factory.py

from vector_stores.chroma_store import ChromaDBStore
from vector_stores.faiss_store import FAISSStore
from config_loader import carregar_config
import sentence_transformers

def get_vector_store(config):
    cfg = carregar_config()                 # new
    emb_model = cfg['embedding']['model']   # new
    device    = cfg['embedding'].get('device', 'cpu')

    store_type = config.get('type')
    if store_type == "chroma":
        return ChromaDBStore(
            path=config.get('path'),
            collection_name=config.get('collection_name'),
            embedding_model=emb_model,     # new
            device=device                  # new
        )
    elif store_type == "faiss":
        return FAISSStore(
            path=config.get('path'),
            embedding_model=emb_model,     # new
            device=device                  # new
        )
    else:
        raise ValueError(f"Unknown vector store: {store_type}")
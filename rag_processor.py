# rag_processor.py (versão modificada)

import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
from config_loader import carregar_config

# Carrega a configuração no início do módulo
config = carregar_config()
pdf_config = config['pdf_processing']
db_config = config['chromadb']

def dividir_texto_em_chunks(texto, nome_ficheiro, debug_mode=False):
    """Divide o texto em chunks e associa metadados a cada um."""
    # *** MODIFICADO: Usa valores do config.yaml ***
    tamanho_chunk = pdf_config['chunk_size']
    sobreposicao_chunk = pdf_config['chunk_overlap']

    if not texto:
        if debug_mode:
            st.warning(f"⚠️ DEBUG: Texto vazio para {nome_ficheiro}")
        return [], []
    
    if debug_mode:
        st.write(f"📄 DEBUG: Processando '{nome_ficheiro}':")
        st.write(f"  - Tamanho do texto: {len(texto)} caracteres")
    
    chunks, metadados = [], []
    inicio = 0
    while inicio < len(texto):
        fim = inicio + tamanho_chunk
        chunk = texto[inicio:fim]
        chunks.append(chunk)
        metadados.append({"fonte": nome_ficheiro})
        inicio += tamanho_chunk - sobreposicao_chunk
    
    if debug_mode:
        st.write(f"  - Gerados {len(chunks)} chunks")
    return chunks, metadados

def criar_e_armazenar_embeddings(lista_total_chunks, lista_total_metadados):
    """Cria embeddings e os armazena no ChromaDB com metadados."""
    if not lista_total_chunks:
        st.warning("Não há chunks para vetorizar.")
        return None
    try:
        default_ef = embedding_functions.DefaultEmbeddingFunction()
        cliente_chroma = chromadb.Client()
        
        # *** MODIFICADO: Usa o nome da coleção do config.yaml ***
        collection_name = db_config['collection_name']
        
        if collection_name in [c.name for c in cliente_chroma.list_collections()]:
             cliente_chroma.delete_collection(name=collection_name)
        colecao = cliente_chroma.get_or_create_collection(name=collection_name, embedding_function=default_ef)
        
        st.info(f"Vetorizando e armazenando {len(lista_total_chunks)} chunks...")
        ids = [f"chunk_{i}" for i in range(len(lista_total_chunks))]
        colecao.add(documents=lista_total_chunks, metadatas=lista_total_metadados, ids=ids)
        st.success("Embeddings e metadados armazenados!")
        return colecao
    except Exception as e:
        st.error(f"Ocorreu um erro durante a criação dos embeddings: {e}")
        return None


def buscar_contexto_relevante(colecao, pergunta, nomes_ficheiros, debug_mode=False, n_results=10):
    """Busca híbrida: semântica + garantia de representação de todos os arquivos."""
    if colecao is None: 
        if debug_mode:
            st.error("❌ DEBUG: Coleção é None!")
        return ""
    
    if debug_mode:
        st.info(f"🔍 DEBUG: Buscando chunks relevantes para: '{pergunta}'")
    
    # Palavras-chave que indicam pedido de overview geral
    palavras_overview = ['overview', 'resumo', 'sumário', 'todos', 'cada', 'cada um', 'all', 'textos']
    eh_overview_geral = any(palavra in pergunta.lower() for palavra in palavras_overview)
    
    try:
        if eh_overview_geral:
            if debug_mode:
                st.info("🔍 DEBUG: Detectado pedido de overview geral - buscando de todos os arquivos")
            contexto, fontes = "", set()
            
            # Para cada arquivo, pega pelo menos 1-2 chunks
            for nome_arquivo in nomes_ficheiros:
                # Busca específica para este arquivo focando em resumo/introdução
                resultados = colecao.query(
                    query_texts=[f"abstract introduction summary conclusion {pergunta}"], 
                    n_results=2,
                    include=["documents", "metadatas"],
                    where={"fonte": nome_arquivo}
                )
                
                if debug_mode:
                    st.write(f"📄 DEBUG: Encontrados {len(resultados['documents'][0])} chunks para {nome_arquivo}")
                
                for doc, meta in zip(resultados['documents'][0], resultados['metadatas'][0]):
                    fonte = meta.get('fonte', 'desconhecida')
                    contexto += f"Fonte: {fonte}\\nConteúdo: {doc}\\n\\n---\\n\\n"
                    fontes.add(fonte)
            
            if debug_mode:
                st.info(f"✅ DEBUG: Garantida representação de {len(fontes)} arquivos de {len(nomes_ficheiros)} totais")
            
        else:
            # Busca semântica normal para perguntas específicas
            if debug_mode:
                st.info("🔍 DEBUG: Busca semântica normal")
            resultados = colecao.query(query_texts=[pergunta], n_results=n_results, include=["documents", "metadatas"])
            
            contexto, fontes = "", set()
            for doc, meta in zip(resultados['documents'][0], resultados['metadatas'][0]):
                fonte = meta.get('fonte', 'desconhecida')
                contexto += f"Fonte: {fonte}\\nConteúdo: {doc}\\n\\n---\\n\\n"
                fontes.add(fonte)
        
        # DEBUG: Mostrar cada chunk encontrado
        if debug_mode:
            with st.expander("🔍 DEBUG: Chunks encontrados na busca"):
                chunks_para_mostrar = resultados['documents'][0] if not eh_overview_geral else []
                metadados_para_mostrar = resultados['metadatas'][0] if not eh_overview_geral else []
                
                for i, (doc, meta) in enumerate(zip(chunks_para_mostrar, metadados_para_mostrar)):
                    fonte = meta.get('fonte', 'desconhecida')
                    st.write(f"**Chunk {i+1}:**")
                    st.write(f"- Fonte: {fonte}")
                    st.write(f"- Tamanho do conteúdo: {len(doc)} caracteres")
                    st.write(f"- Primeiros 200 caracteres: {doc[:200]}...")
                    st.write("---")
        
        if debug_mode:
            st.info(f"✅ DEBUG: Fontes únicas encontradas: {', '.join(sorted(fontes)) if fontes else 'Nenhuma'}")
            st.write(f"📏 DEBUG: Tamanho total do contexto: {len(contexto)} caracteres")
        
        return contexto
        
    except Exception as e:
        if debug_mode:
            st.error(f"❌ DEBUG: Erro na busca: {e}")
        return ""
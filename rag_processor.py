# rag_processor.py (versão final com abstração de vector store)

import streamlit as st
from config_loader import carregar_config

# Carrega a configuração no início do módulo
config = carregar_config()
pdf_config = config['pdf_processing']

# As funções de criação e busca de embeddings foram removidas daqui.
# Agora, este módulo apenas lida com o processamento de texto.

def dividir_texto_em_chunks(texto, nome_ficheiro, debug_mode=False):
    """Divide o texto em chunks e associa metadados a cada um."""
    tamanho_chunk = pdf_config.get('chunk_size', 1000)
    sobreposicao_chunk = pdf_config.get('chunk_overlap', 200)

    # ... (o resto da função permanece igual) ...
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


def buscar_contexto_relevante(vector_store, pergunta, nomes_ficheiros, debug_mode=False):
    """Busca contexto relevante usando a abstração do Vector Store."""
    # Lê o n_results a partir do ficheiro de configuração
    # inside buscar_contexto_relevante(...)
    n_results = carregar_config()['pdf_processing']['n_results']

    if vector_store is None:
        if debug_mode:
            st.error("❌ DEBUG: Vector Store é None!")
        return ""

    if debug_mode:
        st.info(f"🔍 DEBUG: Buscando chunks para: '{pergunta}' (n_results={n_results})")

    palavras_overview = ['overview', 'resumo', 'sumário', 'todos', 'cada', 'cada um', 'all', 'textos']
    eh_overview_geral = any(palavra in pergunta.lower() for palavra in palavras_overview)

    contexto_final = ""
    fontes_final = set()
    resultados_para_debug = None # Variavel para guardar os resultados para o expander de debug

    try:
        if eh_overview_geral:
            if debug_mode:
                st.info("🔍 DEBUG: Detectado pedido de overview geral - buscando de todos os arquivos")

            for nome_arquivo in nomes_ficheiros:
                # Onde clause só funciona com ChromaDB, então verificamos se o método suporta
                try:
                    resultados = vector_store.buscar(
                        query_texts=f"abstract introduction summary conclusion {pergunta}",
                        n_results=2,
                        where={"fonte": nome_arquivo}
                    )
                except TypeError: # Se o 'where' não for suportado (como no FAISS)
                    resultados = vector_store.buscar(
                        query_texts=f"abstract introduction summary conclusion {pergunta}",
                        n_results=2
                    )

                if debug_mode:
                    st.write(f"📄 DEBUG: Encontrados {len(resultados.get('documents', [[]])[0])} chunks para {nome_arquivo}")

                contexto, fontes = _formatar_resultados_da_busca(resultados)
                contexto_final += contexto
                fontes_final.update(fontes)

            if debug_mode:
                st.info(f"✅ DEBUG: Garantida representação de {len(fontes_final)} arquivos de {len(nomes_ficheiros)} totais")

        else:
            # Busca semântica normal
            if debug_mode:
                st.info("🔍 DEBUG: Busca semântica normal")
            resultados = vector_store.buscar(query_texts=pergunta, n_results=n_results)
            contexto_final, fontes_final = _formatar_resultados_da_busca(resultados)
            resultados_para_debug = resultados # Guarda para o debug

        if debug_mode:
            with st.expander("🔍 DEBUG: Chunks encontrados na busca"):
                # A variável 'resultados' pode não estar definida no fluxo de overview, então verificamos
                if resultados_para_debug and resultados_para_debug.get('documents'):
                    for i, (doc, meta) in enumerate(zip(resultados_para_debug['documents'][0], resultados_para_debug['metadatas'][0])):
                        fonte = meta.get('fonte', 'desconhecida')
                        st.write(f"**Chunk {i+1}:**")
                        st.write(f"- Fonte: {fonte}")
                        st.write(f"- Tamanho do conteúdo: {len(doc)} caracteres")
                        st.write(f"- Primeiros 200 caracteres: {doc[:200]}...")
                        st.write("---")

        if debug_mode:
            st.info(f"✅ DEBUG: Fontes únicas encontradas: {', '.join(sorted(fontes_final)) if fontes_final else 'Nenhuma'}")
            st.write(f"📏 DEBUG: Tamanho total do contexto: {len(contexto_final)} caracteres")

        return contexto_final

    except Exception as e:
        if debug_mode:
            st.error(f"❌ DEBUG: Erro na busca: {e}")
        return ""


def _formatar_resultados_da_busca(resultados):
    """Função auxiliar para formatar os resultados da busca."""
    contexto, fontes = "", set()
    if not resultados or not resultados.get('documents') or not resultados['documents'][0]:
        return contexto, fontes

    for doc, meta in zip(resultados['documents'][0], resultados['metadatas'][0]):
        fonte = meta.get('fonte', 'desconhecida')
        contexto += f"Fonte: {fonte}\nConteúdo: {doc}\n\n---\n\n"
        fontes.add(fonte)
    
    return contexto, fontes
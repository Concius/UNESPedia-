import streamlit as st
import pypdf
import io
import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai

# --- FUNÇÕES DE PROCESSAMENTO (LÓGICA) ---

def dividir_texto_em_chunks(texto, nome_ficheiro, tamanho_chunk=1000, sobreposicao_chunk=200):
    """Divide o texto em chunks e associa metadados a cada um."""
    if not texto:
        st.warning(f"⚠️ DEBUG: Texto vazio para {nome_ficheiro}")
        return [], []
    
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
        if "artigos" in [c.name for c in cliente_chroma.list_collections()]:
             cliente_chroma.delete_collection(name="artigos")
        colecao = cliente_chroma.get_or_create_collection(name="artigos", embedding_function=default_ef)
        
        st.info(f"Vetorizando e armazenando {len(lista_total_chunks)} chunks...")
        ids = [f"chunk_{i}" for i in range(len(lista_total_chunks))]
        colecao.add(documents=lista_total_chunks, metadatas=lista_total_metadados, ids=ids)
        st.success("Embeddings e metadados armazenados!")
        return colecao
    except Exception as e:
        st.error(f"Ocorreu um erro durante a criação dos embeddings: {e}")
        return None

def buscar_contexto_relevante(colecao, pergunta, nomes_ficheiros, n_results=10):
    """Busca híbrida: semântica + garantia de representação de todos os arquivos."""
    if colecao is None: 
        st.error("❌ DEBUG: Coleção é None!")
        return ""
    
    st.info(f"🔍 DEBUG: Buscando chunks relevantes para: '{pergunta}'")
    
    # Palavras-chave que indicam pedido de overview geral
    palavras_overview = ['overview', 'resumo', 'sumário', 'todos', 'cada', 'cada um', 'all', 'textos']
    eh_overview_geral = any(palavra in pergunta.lower() for palavra in palavras_overview)
    
    try:
        if eh_overview_geral:
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
                
                st.write(f"📄 DEBUG: Encontrados {len(resultados['documents'][0])} chunks para {nome_arquivo}")
                
                for doc, meta in zip(resultados['documents'][0], resultados['metadatas'][0]):
                    fonte = meta.get('fonte', 'desconhecida')
                    contexto += f"Fonte: {fonte}\nConteúdo: {doc}\n\n---\n\n"
                    fontes.add(fonte)
            
            st.info(f"✅ DEBUG: Garantida representação de {len(fontes)} arquivos de {len(nomes_ficheiros)} totais")
            
        else:
            # Busca semântica normal para perguntas específicas
            st.info("🔍 DEBUG: Busca semântica normal")
            resultados = colecao.query(query_texts=[pergunta], n_results=n_results, include=["documents", "metadatas"])
            
            contexto, fontes = "", set()
            for doc, meta in zip(resultados['documents'][0], resultados['metadatas'][0]):
                fonte = meta.get('fonte', 'desconhecida')
                contexto += f"Fonte: {fonte}\nConteúdo: {doc}\n\n---\n\n"
                fontes.add(fonte)
        
        # DEBUG: Mostrar cada chunk encontrado
        with st.expander("🔍 DEBUG: Chunks encontrados na busca"):
            for i, (doc, meta) in enumerate(zip(resultados['documents'][0] if not eh_overview_geral else [], resultados['metadatas'][0] if not eh_overview_geral else [])):
                fonte = meta.get('fonte', 'desconhecida')
                st.write(f"**Chunk {i+1}:**")
                st.write(f"- Fonte: {fonte}")
                st.write(f"- Tamanho do conteúdo: {len(doc)} caracteres")
                st.write(f"- Primeiros 200 caracteres: {doc[:200]}...")
                st.write("---")
        
        st.info(f"✅ DEBUG: Fontes únicas encontradas: {', '.join(sorted(fontes)) if fontes else 'Nenhuma'}")
        st.write(f"📏 DEBUG: Tamanho total do contexto: {len(contexto)} caracteres")
        
        return contexto
        
    except Exception as e:
        st.error(f"❌ DEBUG: Erro na busca: {e}")
        return ""

def gerar_resposta_com_llm(contexto, pergunta, api_key, nomes_ficheiros, historico_chat):
    """Envia o prompt para o Gemini e retorna a resposta, agora com memória."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # DEBUG: Mostrar informações sobre os arquivos processados
        st.write("📁 DEBUG: Arquivos que foram processados:")
        for i, nome in enumerate(nomes_ficheiros):
            st.write(f"  {i+1}. {nome}")
        
        # NOVO: Formata o histórico do chat para incluir no prompt
        historico_formatado = "\n".join([f"{msg['role']}: {msg['content']}" for msg in historico_chat])
        
        # DEBUG: Mostrar tamanho do histórico
        st.write(f"💬 DEBUG: Histórico tem {len(historico_chat)} mensagens")

        prompt = f"""
        **Instruções:** Você é um assistente de pesquisa. Responda à "Última pergunta do usuário" baseando-se no "Contexto" e no "Histórico da Conversa".
        Os ficheiros carregados pelo usuário são: {', '.join(nomes_ficheiros)}.

        **Histórico da Conversa:**
        {historico_formatado}

        **Contexto extraído dos documentos (use para basear a sua resposta):**
        ---
        {contexto}
        ---

        **Última pergunta do usuário:** {pergunta}

        **Sua Resposta:**
        """
        
        # DEBUG: Mostrar o prompt completo
        with st.expander("🤖 DEBUG: Prompt enviado para o LLM"):
            st.text(prompt)
            st.write(f"📏 Tamanho total do prompt: {len(prompt)} caracteres")
        
        resposta = model.generate_content(prompt)
        
        # DEBUG: Mostrar resposta
        st.write(f"✅ DEBUG: LLM respondeu com {len(resposta.text)} caracteres")
        
        return resposta.text
    except Exception as e:
        st.error(f"Erro ao comunicar com a API do Gemini: {e}")
        return "Desculpe, ocorreu um erro ao tentar gerar a resposta."

# --- INTERFACE DA APLICAÇÃO (UI) ---

st.set_page_config(page_title="RAG Acadêmico", layout="wide", page_icon="🔬")
st.title("🔬 RAG Acadêmico: Converse com seus Artigos")

with st.sidebar:
    st.header("1. Configuração")
    google_api_key = st.text_input("Sua Chave API do Google AI Studio", key="google_api_key", type="password")
    
    st.header("2. Documentos")
    arquivos_pdf = st.file_uploader("Carregue seus artigos em PDF", type="pdf", accept_multiple_files=True)

    if st.button("Processar Documentos", key="processar_docs"):
        if not arquivos_pdf:
            st.warning("Por favor, carregue ao menos um arquivo PDF.")
        else:
            # CORREÇÃO: Inicializa as listas aqui para garantir que elas existam
            lista_total_chunks, lista_total_metadados, nomes_ficheiros = [], [], []
            with st.spinner("A processar documentos..."):
                for arquivo_pdf in arquivos_pdf:
                    st.write(f"A processar {arquivo_pdf.name}...")
                    nomes_ficheiros.append(arquivo_pdf.name)
                    leitor_pdf = pypdf.PdfReader(io.BytesIO(arquivo_pdf.getvalue()))
                    texto_pdf = "".join(p.extract_text() or "" for p in leitor_pdf.pages)
                    chunks, metadados = dividir_texto_em_chunks(texto_pdf, arquivo_pdf.name)
                    lista_total_chunks.extend(chunks)
                    lista_total_metadados.extend(metadados)

                colecao_vetorial = criar_e_armazenar_embeddings(lista_total_chunks, lista_total_metadados)
                st.session_state.colecao = colecao_vetorial
                st.session_state.nomes_ficheiros = nomes_ficheiros
                st.session_state.documentos_processados = True
                st.session_state.messages = [] 
            st.success("Documentos processados e prontos!")

# --- ÁREA PRINCIPAL DO CHAT ---

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if "documentos_processados" in st.session_state and st.session_state.documentos_processados:
    if prompt_usuario := st.chat_input("Faça uma pergunta sobre os seus documentos..."):
        # Adiciona a mensagem do usuário ao histórico ANTES de gerar a resposta
        st.session_state.messages.append({"role": "user", "content": prompt_usuario})
        with st.chat_message("user"):
            st.markdown(prompt_usuario)

        with st.chat_message("assistant"):
            if not google_api_key:
                st.error("Por favor, insira a sua chave de API do Google na barra lateral.")
            else:
                with st.spinner("A pensar..."):
                    contexto = buscar_contexto_relevante(st.session_state.colecao, prompt_usuario, st.session_state.nomes_ficheiros)
                    # MODIFICADO: Passa o histórico da conversa para a função de geração
                    resposta = gerar_resposta_com_llm(contexto, prompt_usuario, google_api_key, st.session_state.nomes_ficheiros, st.session_state.messages)
                    st.markdown(resposta)
                    st.session_state.messages.append({"role": "assistant", "content": resposta})
else:
    st.info("👋 Bem-vindo! Para começar, insira a sua chave de API, carregue os seus PDFs e clique em 'Processar Documentos' na barra lateral.")
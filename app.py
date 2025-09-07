import streamlit as st
import pypdf
import io
import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai

# --- FUNÇÕES DE PROCESSAMENTO (LÓGICA) ---

def dividir_texto_em_chunks(texto, nome_ficheiro, debug_mode=False, tamanho_chunk=1000, sobreposicao_chunk=200):
    """Divide o texto em chunks e associa metadados a cada um."""
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
                    contexto += f"Fonte: {fonte}\nConteúdo: {doc}\n\n---\n\n"
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
                contexto += f"Fonte: {fonte}\nConteúdo: {doc}\n\n---\n\n"
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

def gerar_resposta_com_llm(contexto, pergunta, api_key, nomes_ficheiros, historico_chat, debug_mode=False, temperature=0.7, top_p=0.95, top_k=40, max_output_tokens=2048):
    """Envia o prompt para o Gemini com parâmetros configuráveis."""
    try:
        genai.configure(api_key=api_key)
        
        # Configuração do modelo com parâmetros personalizáveis
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens,
        )
        
        #Verificação do que está sendo enviado para a API
        st.caption(f"🔧 **Config enviado para API:** T={temperature}, P={top_p}, K={top_k}, Max={max_output_tokens}")
        
        model = genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)
        
        if debug_mode:
            st.write("📁 DEBUG: Arquivos que foram processados:")
            for i, nome in enumerate(nomes_ficheiros):
                st.write(f"  {i+1}. {nome}")
        
        # Formata o histórico do chat
        historico_formatado = "\n".join([f"{msg['role']}: {msg['content']}" for msg in historico_chat])
        
        if debug_mode:
            st.write(f"💬 DEBUG: Histórico tem {len(historico_chat)} mensagens")
            st.write(f"🎛️ DEBUG: Parâmetros do LLM - Temperature: {temperature}, Top-p: {top_p}, Top-k: {top_k}, Max tokens: {max_output_tokens}")

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
        
        if debug_mode:
            with st.expander("🤖 DEBUG: Prompt enviado para o LLM"):
                st.text(prompt)
                st.write(f"📏 Tamanho total do prompt: {len(prompt)} caracteres")
        
        resposta = model.generate_content(prompt)
        
        # NOVO: Após gerar a resposta, mostrar metadados se disponível
        if hasattr(resposta, 'usage_metadata'):
            st.caption(f"📊 **Usage API:** {resposta.usage_metadata}")
        
        if debug_mode:
            st.write(f"✅ DEBUG: LLM respondeu com {len(resposta.text)} caracteres")
            # Tentar mostrar mais detalhes da resposta
            if hasattr(resposta, 'candidates'):
                st.write(f"🔍 DEBUG: Número de candidatos: {len(resposta.candidates)}")
        
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
    
    # NOVO: Controle de Debug
    debug_mode = st.checkbox("🐛 Modo Debug", value=False, help="Mostra informações detalhadas sobre o processamento")
    
    # NOVO: Parâmetros do LLM
    with st.expander("🤖 Parâmetros do LLM"):
        temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.1, 
                               help="Controla a criatividade. Valores baixos = mais conservador, altos = mais criativo")
        
        top_p = st.slider("Top-p (Nucleus Sampling)", min_value=0.0, max_value=1.0, value=0.95, step=0.05,
                         help="Considera apenas os tokens com probabilidade cumulativa até este valor")
        
        top_k = st.slider("Top-k", min_value=1, max_value=100, value=40, step=1,
                         help="Considera apenas os k tokens mais prováveis")
        
        max_output_tokens = st.slider("Max Output Tokens", min_value=100, max_value=8000, value=2048, step=100,
                                    help="Número máximo de tokens na resposta")
        
        # Botão para resetar parâmetros
        if st.button("↺ Resetar Parâmetros"):
            st.rerun()
    
    st.header("2. Documentos")

    arquivos_pdf = st.file_uploader("Carregue seus artigos em PDF", type="pdf", accept_multiple_files=True)

    if st.button("Processar Documentos", key="processar_docs"):
        if not arquivos_pdf:
            st.warning("Por favor, carregue ao menos um arquivo PDF.")
        else:
            # Inicializa as listas
            lista_total_chunks, lista_total_metadados, nomes_ficheiros = [], [], []
            with st.spinner("A processar documentos..."):
                for arquivo_pdf in arquivos_pdf:
                    st.write(f"A processar {arquivo_pdf.name}...")
                    nomes_ficheiros.append(arquivo_pdf.name)
                    leitor_pdf = pypdf.PdfReader(io.BytesIO(arquivo_pdf.getvalue()))
                    texto_pdf = "".join(p.extract_text() or "" for p in leitor_pdf.pages)
                    
                    # AQUI: Passando o debug_mode
                    chunks, metadados = dividir_texto_em_chunks(texto_pdf, arquivo_pdf.name, debug_mode)
                    
                    lista_total_chunks.extend(chunks)
                    lista_total_metadados.extend(metadados)

                colecao_vetorial = criar_e_armazenar_embeddings(lista_total_chunks, lista_total_metadados)
                st.session_state.colecao = colecao_vetorial
                st.session_state.nomes_ficheiros = nomes_ficheiros
                st.session_state.documentos_processados = True
                st.session_state.messages = [] 
            st.success("Documentos processados e prontos!")
    
    if st.button("🧪 Teste REAL dos Parâmetros"):
        st.session_state.teste_real = True
    
    if st.button("🎨 Teste CRIATIVO dos Parâmetros"):
        st.session_state.teste_criativo = True

# --- ÁREA PRINCIPAL DO CHAT ---
if "teste_real" in st.session_state and st.session_state.teste_real:
    st.session_state.teste_real = False
    
    if google_api_key:
        st.write("### 🧪 Teste Real dos Parâmetros")
        
        # Teste 1: Temperature baixa
        st.write("**Teste 1: Temperature = 0.0 (deve ser determinístico)**")
        for i in range(3):
            with st.spinner(f"Gerando resposta {i+1}/3..."):
                resposta_baixa = gerar_resposta_com_llm(
                    "", 
                    "Complete: O céu é", 
                    google_api_key, 
                    [], 
                    [], 
                    False,  # debug_mode
                    0.0,    # temperature baixa
                    0.95, 40, 50  # outros parâmetros
                )
                st.write(f"Resposta {i+1}: {resposta_baixa}")
        
        st.write("**Teste 2: Temperature = 1.8 (deve ser criativo/variado)**")
        for i in range(3):
            with st.spinner(f"Gerando resposta {i+1}/3..."):
                resposta_alta = gerar_resposta_com_llm(
                    "", 
                    "Complete: O céu é", 
                    google_api_key, 
                    [], 
                    [], 
                    False,  # debug_mode
                    1.8,    # temperature alta
                    0.95, 40, 50  # outros parâmetros
                )
                st.write(f"Resposta {i+1}: {resposta_alta}")
                
        st.success("✅ Se as respostas do Teste 1 forem muito similares e as do Teste 2 forem bem diferentes, os parâmetros estão funcionando!")
    else:
        st.error("Precisa da API key para testar!")

if "teste_criativo" in st.session_state and st.session_state.teste_criativo:
    st.session_state.teste_criativo = False
    
    if google_api_key:
        st.write("### 🎨 Teste Criativo dos Parâmetros")
        
        pergunta_criativa = "Isso não tem nada haver com os textos. Qual o melhor sabor de sorvete? Sua resposta de conter um sabor"
        
        # Teste 1: Temperature baixa
        st.write("**Temperature = 0.0 (conservador):**")
        for i in range(3):
            resposta = gerar_resposta_com_llm("", pergunta_criativa, google_api_key, [], [], False, 0.0, 0.95, 40, 100)
            st.write(f"• {resposta}")
        
        # Teste 2: Temperature alta
        st.write("**Temperature = 1.9 (criativo):**")
        for i in range(3):
            resposta = gerar_resposta_com_llm("", pergunta_criativa, google_api_key, [], [], False, 1.9, 0.95, 40, 100)
            st.write(f"• {resposta}")

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
                    contexto = buscar_contexto_relevante(st.session_state.colecao, prompt_usuario, st.session_state.nomes_ficheiros, debug_mode)
                    # MODIFICADO: Passa o histórico da conversa para a função de geração
                    resposta = gerar_resposta_com_llm(contexto, prompt_usuario, google_api_key, st.session_state.nomes_ficheiros, st.session_state.messages, debug_mode, temperature, top_p, top_k, max_output_tokens)
                    st.markdown(resposta)
                    st.session_state.messages.append({"role": "assistant", "content": resposta})
else:
    st.info("👋 Bem-vindo! Para começar, insira a sua chave de API, carregue os seus PDFs e clique em 'Processar Documentos' na barra lateral.")
import streamlit as st
import pypdf
import io

from rag_processor import dividir_texto_em_chunks, criar_e_armazenar_embeddings, buscar_contexto_relevante
from llm_handler import gerar_resposta_com_llm
from config_loader import carregar_config

# --- CARREGA CONFIGURAÇÃO ---
config = carregar_config()
if config is None:
    st.stop() # Interrompe a execução se o config não for carregado
llm_config = config['llm_defaults']


# --- INTERFACE DA APLICAÇÃO (UI) ---

st.set_page_config(page_title="RAG Acadêmico", layout="wide", page_icon="🔬")
st.title("🔬 RAG Acadêmico: Converse com seus Artigos")

with st.sidebar:
    st.header("1. Configuração")
    google_api_key = st.text_input("Sua Chave API do Google AI Studio", key="google_api_key", type="password")
    
    debug_mode = st.checkbox("🐛 Modo Debug", value=False, help="Mostra informações detalhadas sobre o processamento")
    
    # *** MODIFICADO: Usa valores do config.yaml como padrão para os sliders ***
    with st.expander("🤖 Parâmetros do LLM"):
        temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=llm_config['temperature'], step=0.1, 
                               help="Controla a criatividade. Valores baixos = mais conservador, altos = mais criativo")
        
        top_p = st.slider("Top-p (Nucleus Sampling)", min_value=0.0, max_value=1.0, value=llm_config['top_p'], step=0.05,
                         help="Considera apenas os tokens com probabilidade cumulativa até este valor")
        
        top_k = st.slider("Top-k", min_value=1, max_value=100, value=llm_config['top_k'], step=1,
                         help="Considera apenas os k tokens mais prováveis")
        
        max_output_tokens = st.slider("Max Output Tokens", min_value=100, max_value=8000, value=llm_config['max_output_tokens'], step=100,
                                    help="Número máximo de tokens na resposta")
        
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
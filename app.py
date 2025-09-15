# app.py (versão modificada)

import streamlit as st
import pypdf
import io

# Importa as funções dos módulos
from rag_processor import dividir_texto_em_chunks, criar_e_armazenar_embeddings, buscar_contexto_relevante
from llm_handler import gerar_resposta_com_llm
from config_loader import carregar_config

# --- CARREGA CONFIGURAÇÃO ---
config = carregar_config()
if config is None:
    st.stop()
llm_config = config['llm_defaults']
providers_config = config['llm_providers']


# --- INTERFACE DA APLICAÇÃO (UI) ---

st.set_page_config(page_title="RAG Acadêmico", layout="wide", page_icon="🔬")
st.title("🔬 RAG Acadêmico: Converse com seus Artigos")

with st.sidebar:
    st.header("1. Configuração do LLM")
    
    # *** MODIFICADO: Seletor de Provedor ***
    lista_provedores = list(providers_config.keys())
    provedor_selecionado = st.selectbox("Escolha o Provedor de LLM:", lista_provedores)

    # *** MODIFICADO: Pega a API Key e o modelo do provedor selecionado ***
    config_provedor_atual = providers_config[provedor_selecionado]
    api_key_padrao = config_provedor_atual.get('api_key', '')
    modelo_padrao = config_provedor_atual.get('model', '')

    st.write(f"Modelo Padrão: `{modelo_padrao}`")
    api_key = st.text_input(f"Sua Chave API para {provedor_selecionado}", value=api_key_padrao, type="password", key=f"api_key_{provedor_selecionado}")

    debug_mode = st.checkbox("🐛 Modo Debug", value=False)
    
    with st.expander("🤖 Parâmetros de Geração"):
        temperature = st.slider("Temperature", 0.0, 2.0, llm_config['temperature'], 0.1)
        top_p = st.slider("Top-p", 0.0, 1.0, llm_config['top_p'], 0.05)
        top_k = st.slider("Top-k", 1, 100, llm_config['top_k'], 1)
        max_output_tokens = st.slider("Max Output Tokens", 100, 8000, llm_config['max_output_tokens'], 100)

    # ... (O resto da sidebar com o upload de documentos permanece igual) ...
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

# --- ÁREA PRINCIPAL DO CHAT ---
# ... (A lógica de exibição do histórico de chat permanece a mesma) ...

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if "documentos_processados" in st.session_state and st.session_state.documentos_processados:
    if prompt_usuario := st.chat_input("Faça uma pergunta sobre os seus documentos..."):
        st.session_state.messages.append({"role": "user", "content": prompt_usuario})
        with st.chat_message("user"):
            st.markdown(prompt_usuario)

        with st.chat_message("assistant"):
            if not api_key or "SUA_CHAVE" in api_key:
                st.error(f"Por favor, insira uma chave de API válida para {provedor_selecionado} na barra lateral.")
            else:
                with st.spinner("A pensar..."):
                    contexto = buscar_contexto_relevante(st.session_state.colecao, prompt_usuario, st.session_state.nomes_ficheiros, debug_mode)
                    
                    # *** MODIFICADO: Chamada unificada para o llm_handler ***
                    config_geracao = {
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k,
                        "max_output_tokens": max_output_tokens,
                    }
                    
                    resposta = gerar_resposta_com_llm(
                        provider_name=provedor_selecionado,
                        api_key=api_key,
                        model_config=config_provedor_atual,
                        contexto=contexto,
                        pergunta=prompt_usuario,
                        historico_chat=st.session_state.messages,
                        nomes_ficheiros=st.session_state.nomes_ficheiros,
                        config_geracao=config_geracao
                    )
                    st.markdown(resposta)
                    st.session_state.messages.append({"role": "assistant", "content": resposta})
else:
    st.info("👋 Bem-vindo! Escolha um provedor, insira sua chave de API, carregue seus PDFs e clique em 'Processar Documentos'.")
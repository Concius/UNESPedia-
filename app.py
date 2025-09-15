# app.py (versão final com seletor de Vector Store)

import streamlit as st
import pypdf
import io

# Importa as funções dos módulos de lógica
from config_loader import carregar_config
from llm_handler import gerar_resposta_com_llm
from rag_processor import dividir_texto_em_chunks, buscar_contexto_relevante
from vector_store_factory import get_vector_store

# --- CARREGA CONFIGURAÇÃO ---
config = carregar_config()
if config is None:
    st.stop()

llm_config = config['llm_defaults']
providers_config = config['llm_providers']
presets_config = config.get('llm_presets', {})
vector_stores_config = config['vector_stores'] # Carrega todas as configs de vector stores


# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO (SESSION STATE) ---

# Garante que os valores dos parâmetros do LLM existam no estado da sessão
if 'temperature' not in st.session_state:
    st.session_state.temperature = llm_config['temperature']
# ... (outras inicializações de parâmetros do LLM como antes) ...
if 'top_p' not in st.session_state:
    st.session_state.top_p = llm_config['top_p']
if 'top_k' not in st.session_state:
    st.session_state.top_k = llm_config['top_k']
if 'max_output_tokens' not in st.session_state:
    st.session_state.max_output_tokens = llm_config['max_output_tokens']

# Inicializa o histórico de mensagens se não existir
if "messages" not in st.session_state:
    st.session_state.messages = []


# --- INTERFACE DA APLICAÇÃO (UI) ---

st.set_page_config(page_title="RAG Acadêmico", layout="wide", page_icon="🔬")
st.title("🔬 RAG Acadêmico: Converse com seus Artigos")

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    # --- SECÇÃO DE DOCUMENTOS E VECTOR STORE ---
    st.header("1. Base de Conhecimento")
    
    # MODIFICADO: Adiciona o seletor para o Vector Store
    lista_vector_stores = list(vector_stores_config.keys())
    # A chave do selectbox está ligada a uma função para recarregar o store se ele mudar
    if 'vector_store_choice' not in st.session_state:
        st.session_state.vector_store_choice = lista_vector_stores[0]

    def on_vector_store_change():
        # Se a escolha mudar, apaga a instância antiga do estado da sessão
        # para forçar a recriação da nova instância.
        if 'vector_store' in st.session_state:
            del st.session_state['vector_store']
    
    st.selectbox(
        "Escolha o Vector Store:", 
        lista_vector_stores, 
        key='vector_store_choice',
        on_change=on_vector_store_change
    )
    
    # Carrega o vector store escolhido se ele ainda não estiver carregado
    if 'vector_store' not in st.session_state:
        with st.spinner(f"A carregar {st.session_state.vector_store_choice}..."):
            config_vs_atual = vector_stores_config[st.session_state.vector_store_choice]
            st.session_state.vector_store = get_vector_store(config_vs_atual)

    arquivos_pdf = st.file_uploader("Carregue seus artigos em PDF", type="pdf", accept_multiple_files=True)

    if st.button("Processar Documentos", key="processar_docs"):
        # ... (lógica de processamento de documentos igual à anterior) ...
        if not arquivos_pdf:
            st.warning("Por favor, carregue ao menos um arquivo PDF.")
        else:
            # ...
            lista_total_chunks, lista_total_metadados, nomes_ficheiros = [], [], []
            with st.spinner("A processar documentos..."):
                for arquivo_pdf in arquivos_pdf:
                    st.write(f"A processar {arquivo_pdf.name}...")
                    nomes_ficheiros.append(arquivo_pdf.name)
                    leitor_pdf = pypdf.PdfReader(io.BytesIO(arquivo_pdf.getvalue()))
                    texto_pdf = "".join(p.extract_text() or "" for p in leitor_pdf.pages)
                    chunks, metadados = dividir_texto_em_chunks(texto_pdf, arquivo_pdf.name, debug_mode=st.session_state.get('debug_mode', False))
                    lista_total_chunks.extend(chunks)
                    lista_total_metadados.extend(metadados)

                if lista_total_chunks:
                    st.session_state.vector_store.adicionar(lista_total_chunks, lista_total_metadados)
                
                st.session_state.nomes_ficheiros = nomes_ficheiros
                st.session_state.documentos_processados = True
                st.session_state.messages = []
            st.success("Documentos processados e prontos!")

    st.divider()

    # --- SECÇÃO DE CONFIGURAÇÃO DO LLM ---
    st.header("2. Configuração do LLM")
    
    # ... (toda a lógica do seletor de LLM, API key, presets e sliders permanece exatamente a mesma) ...
    lista_provedores = list(providers_config.keys())
    provedor_selecionado = st.selectbox("Escolha o Provedor de LLM:", lista_provedores)
    config_provedor_atual = providers_config[provedor_selecionado]
    api_key_padrao = config_provedor_atual.get('api_key', '')
    modelo_padrao = config_provedor_atual.get('model', '')
    st.write(f"Modelo Padrão: `{modelo_padrao}`")
    session_key_id = f"api_key_input_{provedor_selecionado}"
    if session_key_id not in st.session_state:
        st.session_state[session_key_id] = api_key_padrao
    def api_key_changed():
        nova_key = st.session_state[session_key_id]
        if nova_key and "SUA_CHAVE" not in nova_key:
            st.toast(f"✅ Chave API para {provedor_selecionado} foi inserida!", icon="🔑")
    api_key = st.text_input(f"Sua Chave API para {provedor_selecionado}",value=st.session_state.get(session_key_id, ''),type="password",key=session_key_id,on_change=api_key_changed)
    debug_mode = st.checkbox("🐛 Modo Debug", value=False, key='debug_mode')
    with st.expander("🤖 Parâmetros de Geração", expanded=True):
        st.write("**Presets**")
        cols = st.columns(len(presets_config))
        preset_names = list(presets_config.keys())
        for i, col in enumerate(cols):
            preset_name = preset_names[i]
            if col.button(preset_name, use_container_width=True, key=f"preset_{i}"):
                preset_values = presets_config[preset_name]
                st.session_state.temperature = preset_values['temperature']
                st.session_state.top_p = preset_values['top_p']
                st.session_state.top_k = preset_values['top_k']
                st.rerun()
        st.divider()
        st.slider("Temperature", 0.0, 2.0, key='temperature', step=0.1)
        st.slider("Top-p", 0.0, 1.0, key='top_p', step=0.05)
        st.slider("Top-k", 1, 100, key='top_k', step=1)
        st.slider("Max Output Tokens", 100, 8000, key='max_output_tokens', step=100)

# --- ÁREA PRINCIPAL DO CHAT ---
# (Esta secção não sofre alterações)
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
                    contexto = buscar_contexto_relevante(
                        vector_store=st.session_state.vector_store,
                        pergunta=prompt_usuario,
                        nomes_ficheiros=st.session_state.get('nomes_ficheiros', []),
                        debug_mode=st.session_state.get('debug_mode', False)
                    )
                    config_geracao = {
                        "temperature": st.session_state.temperature,
                        "top_p": st.session_state.top_p,
                        "top_k": st.session_state.top_k,
                        "max_output_tokens": st.session_state.max_output_tokens,
                    }
                    resposta = gerar_resposta_com_llm(
                        provider_name=provedor_selecionado,
                        api_key=api_key,
                        model_config=config_provedor_atual,
                        contexto=contexto,
                        pergunta=prompt_usuario,
                        historico_chat=st.session_state.messages,
                        nomes_ficheiros=st.session_state.get('nomes_ficheiros', []),
                        config_geracao=config_geracao
                    )
                    st.markdown(resposta)
                    st.session_state.messages.append({"role": "assistant", "content": resposta})
else:
    st.info("👋 Bem-vindo! Escolha seu Vector Store e LLM, insira sua chave de API, carregue seus PDFs e clique em 'Processar Documentos'.")
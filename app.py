# app.py (versão final com UX melhorada e correção de bugs)

import streamlit as st
import pypdf
import io

# Importa as funções dos módulos de lógica
from config_loader import carregar_config
from llm_handler import gerar_resposta_com_llm
from rag_processor import dividir_texto_em_chunks, buscar_contexto_relevante
from vector_store_factory import get_vector_store
import chat_manager

# --- LAYOUT E CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="RAG Acadêmico", layout="wide", page_icon="🔬")

# Aplica CSS para os botões de controlo das mensagens e para fixar o input no fundo
st.markdown("""
    <style>
        .message-controls {
            display: flex;
            justify-content: flex-end;
            gap: 5px;
            margin-top: -35px;
            margin-right: 5px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .stChatMessage:hover .message-controls {
            opacity: 1;
        }
        .stButton>button {
            background-color: transparent;
            border: none;
            padding: 0 !important;
            font-size: 1em;
            color: #808080;
        }
        .stButton>button:hover {
            color: #FFFFFF;
            transform: scale(1.1);
        }
    </style>
""", unsafe_allow_html=True)

# --- CARREGA CONFIGURAÇÃO ---
config = carregar_config()
if config is None:
    st.stop()

llm_config = config['llm_defaults']
providers_config = config['llm_providers']
presets_config = config.get('llm_presets', {})
vector_stores_config = config['vector_stores']


# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO (SESSION STATE) ---
default_states = {
    'temperature': llm_config['temperature'], 'top_p': llm_config['top_p'],
    'top_k': llm_config['top_k'], 'max_output_tokens': llm_config['max_output_tokens'],
    'vector_store': None, 'vector_store_choice': list(vector_stores_config.keys())[0],
    'messages': [], 'current_chat': "Nova Conversa", 'editing_message_index': None
}
for key, value in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Carrega o vector store apenas uma vez ou quando a escolha muda
if st.session_state.vector_store is None:
    with st.spinner(f"A carregar {st.session_state.vector_store_choice}..."):
        config_vs_atual = vector_stores_config[st.session_state.vector_store_choice]
        st.session_state.vector_store = get_vector_store(config_vs_atual)

# --- FUNÇÕES DE LÓGICA DO CHAT ---
def handle_user_input(prompt):
    """Adiciona a mensagem do user e gera a resposta do assistente."""
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Obtém a configuração necessária para a chamada à API
    provedor = st.session_state.get('provedor_selecionado', list(providers_config.keys())[0])
    config_provedor = providers_config[provedor]
    session_key = f"api_key_input_{provedor}"
    api_key = st.session_state.get(session_key, '')

    if not api_key or "SUA_CHAVE" in api_key:
        st.error(f"Por favor, insira uma chave de API válida para {provedor} na barra lateral.")
        st.session_state.messages.pop()
        return

    # Gera a resposta do assistente
    contexto = buscar_contexto_relevante(
        vector_store=st.session_state.vector_store, pergunta=prompt,
        nomes_ficheiros=st.session_state.get('nomes_ficheiros', []),
        debug_mode=st.session_state.get('debug_mode', False)
    )
    config_geracao = {
        "temperature": st.session_state.temperature, "top_p": st.session_state.top_p,
        "top_k": st.session_state.top_k, "max_output_tokens": st.session_state.max_output_tokens,
    }
    resposta = gerar_resposta_com_llm(
        provider_name=provedor, api_key=api_key, model_config=config_provedor,
        contexto=contexto, pergunta=prompt, historico_chat=st.session_state.messages[:-1],
        nomes_ficheiros=st.session_state.get('nomes_ficheiros', []), config_geracao=config_geracao
    )
    st.session_state.messages.append({"role": "assistant", "content": resposta})

def handle_regenerate():
    """Remove o último par de mensagens e gera uma nova resposta."""
    if len(st.session_state.messages) >= 2 and st.session_state.messages[-1]['role'] == 'assistant':
        last_user_prompt = st.session_state.messages[-2]['content']
        st.session_state.messages = st.session_state.messages[:-2]
        handle_user_input(last_user_prompt)

# --- LAYOUT PRINCIPAL ---
st.title("🔬 RAG Acadêmico: Converse com seus Artigos")

# O container do chat irá crescer para preencher o espaço
chat_container = st.container()

with chat_container:
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if st.session_state.editing_message_index == i:
                # ---- LÓGICA DE EDIÇÃO ----
                edited_content = st.text_area("", value=message["content"], key=f"edit_area_{i}", height=150)
                col1, col2 = st.columns([1, 1])
                if col1.button("✅ Salvar", key=f"save_edit_{i}", use_container_width=True):
                    st.session_state.messages[i]["content"] = edited_content
                    st.session_state.editing_message_index = None
                    st.rerun()
                if col2.button("❌ Cancelar", key=f"cancel_edit_{i}", use_container_width=True):
                    st.session_state.editing_message_index = None
                    st.rerun()
            else:
                # ---- MENSAGEM NORMAL COM BOTÕES DE CONTROLO ----
                st.markdown(message["content"])
                st.markdown(f"""
                    <div class="message-controls">
                        <button onclick="document.querySelector('[data-testid=\"baseButton-secondary\"][key=\"edit_{i}\"]').click()">✏️</button>
                        <button onclick="document.querySelector('[data-testid=\"baseButton-secondary\"][key=\"delete_{i}\"]').click()">🗑️</button>
                    </div>
                """, unsafe_allow_html=True)
                # Botões invisíveis que são acionados pelo javascript acima
                st.button("✏️", key=f"edit_{i}", help="Editar mensagem", on_click=lambda i=i: st.session_state.update(editing_message_index=i))
                st.button("🗑️", key=f"delete_{i}", help="Apagar mensagem", on_click=lambda i=i: st.session_state.messages.pop(i) and st.rerun())

# INPUT E REGENERATE FICAM NO FUNDO DA PÁGINA
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    st.button("🔄 Regenerar Resposta", on_click=handle_regenerate, use_container_width=True)

if prompt := st.chat_input("Faça uma pergunta...", key="main_chat_input"):
    if st.session_state.get("documentos_processados"):
        handle_user_input(prompt)
        st.rerun()
    else:
        st.toast("Por favor, processe alguns documentos primeiro.", icon="📄")

if not st.session_state.get("documentos_processados"):
    st.info("👋 Bem-vindo! Carregue documentos ou uma conversa salva na barra lateral para começar.")

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Gerenciar Conversa")
    if st.button("➕ Nova Conversa", use_container_width=True):
        keys_to_reset = ['messages', 'documentos_processados', 'nomes_ficheiros']
        for key in keys_to_reset:
            if key in st.session_state: del st.session_state[key]
        st.session_state.current_chat = "Nova Conversa"
        st.rerun()

    chats_salvos = ["Nova Conversa"] + chat_manager.listar_chats_salvos()
    try:
        current_chat_index = chats_salvos.index(st.session_state.current_chat)
    except ValueError:
        current_chat_index = 0

    def on_chat_change():
        selected_chat = st.session_state.select_chat_widget
        if selected_chat != "Nova Conversa":
            st.session_state.messages = chat_manager.carregar_chat(selected_chat)
            st.session_state.documentos_processados = True 
        else:
            st.session_state.messages = []
            if 'documentos_processados' in st.session_state: del st.session_state['documentos_processados']
        st.session_state.current_chat = selected_chat
    
    st.selectbox("Carregar Conversa:", chats_salvos, index=current_chat_index, key='select_chat_widget', on_change=on_chat_change)
    
    default_save_name = st.session_state.current_chat if st.session_state.current_chat != "Nova Conversa" else chat_manager.gerar_nome_chat_padrao()
    nome_chat_para_salvar = st.text_input("Nome do ficheiro:", value=default_save_name)
    col_save, col_delete = st.columns(2)
    if col_save.button("💾 Salvar", use_container_width=True):
        if nome_chat_para_salvar and st.session_state.messages:
            if chat_manager.salvar_chat(st.session_state.messages, nome_chat_para_salvar):
                st.session_state.current_chat = nome_chat_para_salvar.replace(".json", "")
                st.rerun()
        else:
            st.warning("A conversa está vazia. Nada para salvar.")
    if col_delete.button("🗑️ Apagar", use_container_width=True):
        if st.session_state.current_chat != "Nova Conversa":
            if chat_manager.apagar_chat(st.session_state.current_chat):
                st.session_state.current_chat = "Nova Conversa"
                st.rerun()
        else:
            st.warning("Nenhuma conversa salva selecionada para apagar.")
    st.divider()

    st.header("1. Base de Conhecimento")
    def on_vector_store_change():
        if 'vector_store' in st.session_state: del st.session_state['vector_store']
    st.selectbox("Escolha o Vector Store:", list(vector_stores_config.keys()), key='vector_store_choice', on_change=on_vector_store_change)
    arquivos_pdf = st.file_uploader("Carregue seus artigos em PDF", type="pdf", accept_multiple_files=True)
    if st.button("Processar Documentos", key="processar_docs"):
        if not arquivos_pdf:
            st.warning("Por favor, carregue ao menos um arquivo PDF.")
        else:
            with st.spinner("A processar documentos..."):
                nomes_ficheiros = [f.name for f in arquivos_pdf]
                lista_chunks, lista_metadados = [], []
                for arquivo in arquivos_pdf:
                    texto = "".join(p.extract_text() or "" for p in pypdf.PdfReader(io.BytesIO(arquivo.getvalue())).pages)
                    chunks, metadados = dividir_texto_em_chunks(texto, arquivo.name, st.session_state.get('debug_mode', False))
                    lista_chunks.extend(chunks)
                    lista_metadados.extend(metadados)
                if lista_chunks:
                    st.session_state.vector_store.adicionar(lista_chunks, lista_metadados)
                st.session_state.nomes_ficheiros = nomes_ficheiros
                st.session_state.documentos_processados = True
            st.success("Documentos processados e prontos!")
    st.divider()

    st.header("2. Configuração do LLM")
    provedor_selecionado = st.selectbox("Escolha o Provedor de LLM:", list(providers_config.keys()), key="provedor_selecionado")
    config_provedor_atual = providers_config[provedor_selecionado]
    st.write(f"Modelo Padrão: `{config_provedor_atual.get('model', '')}`")
    session_key_id = f"api_key_input_{provedor_selecionado}"
    if session_key_id not in st.session_state:
        st.session_state[session_key_id] = config_provedor_atual.get('api_key', '')
    def api_key_changed():
        if st.session_state[session_key_id] and "SUA_CHAVE" not in st.session_state[session_key_id]:
            st.toast(f"✅ Chave API para {st.session_state.provedor_selecionado} inserida!", icon="🔑")
    api_key = st.text_input(f"Sua Chave API para {provedor_selecionado}", value=st.session_state.get(session_key_id, ''), type="password", key=session_key_id, on_change=api_key_changed)
    debug_mode = st.checkbox("🐛 Modo Debug", value=False, key='debug_mode')
    with st.expander("🤖 Parâmetros de Geração", expanded=True):
        st.write("**Presets**")
        cols = st.columns(len(presets_config))
        for i, (p_name, p_values) in enumerate(presets_config.items()):
            if cols[i].button(p_name, use_container_width=True, key=f"preset_{i}"):
                st.session_state.temperature, st.session_state.top_p, st.session_state.top_k = p_values['temperature'], p_values['top_p'], p_values['top_k']
                st.rerun()
        st.divider()
        st.slider("Temperature", 0.0, 2.0, key='temperature', step=0.1)
        st.slider("Top-p", 0.0, 1.0, key='top_p', step=0.05)
        st.slider("Top-k", 1, 100, key='top_k', step=1)
        st.slider("Max Output Tokens", 100, 8000, key='max_output_tokens', step=100)
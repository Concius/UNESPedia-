# app.py (versão com UX final e correções)

import streamlit as st
import pypdf
import io

# Importa as funções dos módulos de lógica
from config_loader import carregar_config
from llm_handler import gerar_resposta_com_llm
from rag_processor import dividir_texto_em_chunks, buscar_contexto_relevante
from vector_store_factory import get_vector_store
import chat_manager
import secrets_manager # Novo import

# --- LAYOUT E CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="RAG Acadêmico", layout="wide", page_icon="🔬")

# Aplica CSS para os botões de controlo das mensagens que aparecem ao passar o rato
st.markdown("""
    <style>
        /* Esconde os controlos por defeito */
        .message-controls {
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            position: absolute;
            top: -15px;
            right: 5px;
            opacity: 0;
            transition: opacity 0.2s ease-in-out;
        }
        /* Mostra os controlos quando o rato está sobre a mensagem */
        .stChatMessage:hover .message-controls {
            opacity: 1;
        }
        .stButton>button {
            background-color: #262730; /* Cor de fundo do botão */
            border-radius: 5px;
            padding: 2px 5px !important;
            border: 1px solid #444;
        }
    </style>
""", unsafe_allow_html=True)


# --- CARREGA CONFIGURAÇÃO ---
config = carregar_config()
if config is None: st.stop()

llm_config = config['llm_defaults']
providers_config = config['llm_providers']
presets_config = config.get('llm_presets', {})
vector_stores_config = config['vector_stores']


# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO (SESSION STATE) ---
default_states = {
    'temperature': llm_config['temperature'], 'top_p': llm_config['top_p'],
    'top_k': llm_config['top_k'], 'max_output_tokens': llm_config['max_output_tokens'],
    'vector_store': None, 'vector_store_choice': list(vector_stores_config.keys())[0],
    'messages': [], 'current_chat': "Nova Conversa", 'editing_message_index': None,
    'api_keys': secrets_manager.load_secrets() # Carrega as chaves salvas
}
for key, value in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

if st.session_state.vector_store is None:
    with st.spinner(f"A carregar {st.session_state.vector_store_choice}..."):
        config_vs_atual = vector_stores_config[st.session_state.vector_store_choice]
        st.session_state.vector_store = get_vector_store(config_vs_atual)


# --- FUNÇÕES DE LÓGICA DO CHAT ---
def handle_response_generation(prompt):
    """Função central para gerar e salvar respostas."""
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    provedor = st.session_state.provedor_selecionado
    api_key = st.session_state.api_keys.get(provedor)

    if not api_key:
        st.error(f"Por favor, insira uma chave de API válida para {provedor} na barra lateral.")
        st.session_state.messages.pop()
        return

    with st.chat_message("assistant"):
        placeholder = st.empty()
        with st.spinner("A pensar..."):
            resposta = gerar_resposta_com_llm(
                provider_name=provedor, api_key=api_key, model_config=providers_config[provedor],
                contexto=buscar_contexto_relevante(st.session_state.vector_store, prompt, st.session_state.get('nomes_ficheiros', [])),
                pergunta=prompt, historico_chat=st.session_state.messages[:-1],
                nomes_ficheiros=st.session_state.get('nomes_ficheiros', []),
                config_geracao={"temperature": st.session_state.temperature, "top_p": st.session_state.top_p, "top_k": st.session_state.top_k, "max_output_tokens": st.session_state.max_output_tokens}
            )
            placeholder.markdown(resposta)
            st.session_state.messages.append({"role": "assistant", "content": resposta})

            # SALVAMENTO AUTOMÁTICO
            if st.session_state.current_chat == "Nova Conversa":
                st.session_state.current_chat = chat_manager.gerar_nome_chat_padrao()
            chat_manager.salvar_chat(st.session_state.messages, st.session_state.current_chat)
            st.toast("Conversa salva automaticamente!", icon="💾")

def handle_regenerate():
    if len(st.session_state.messages) >= 2:
        last_user_prompt = st.session_state.messages[-2]['content']
        st.session_state.messages = st.session_state.messages[:-2]
        handle_response_generation(last_user_prompt)

# --- LAYOUT PRINCIPAL ---
st.title("🔬 RAG Acadêmico: Converse com seus Artigos")

# O container do chat irá crescer para preencher o espaço
chat_container = st.container()
with chat_container:
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if st.session_state.editing_message_index == i:
                edited_content = st.text_area("", value=message["content"], key=f"edit_area_{i}", height=150)
                col1, col2 = st.columns([1, 1])
                if col1.button("✅ Salvar", key=f"save_edit_{i}", use_container_width=True):
                    st.session_state.messages[i]["content"] = edited_content
                    st.session_state.editing_message_index = None
                    chat_manager.salvar_chat(st.session_state.messages, st.session_state.current_chat) # Salva ao editar
                    st.rerun()
                if col2.button("❌ Cancelar", key=f"cancel_edit_{i}", use_container_width=True):
                    st.session_state.editing_message_index = None
                    st.rerun()
            else:
                st.markdown(message["content"])
                # Este div vazio é o target para os botões aparecerem
                st.markdown('<div class="message-controls"></div>', unsafe_allow_html=True)
                
    # Botões invisíveis que são posicionados pelo CSS (esta parte fica fora do chat_message)
    for i in range(len(st.session_state.messages)):
        cols = st.columns([0.9, 0.05, 0.05])
        with cols[1]:
            st.button("✏️", key=f"edit_{i}", help="Editar mensagem", on_click=lambda i=i: st.session_state.update(editing_message_index=i))
        with cols[2]:
            st.button("🗑️", key=f"delete_{i}", help="Apagar mensagem", on_click=lambda i=i: (st.session_state.messages.pop(i), chat_manager.salvar_chat(st.session_state.messages, st.session_state.current_chat), st.rerun()))


# INPUT E REGENERATE FICAM NO FUNDO DA PÁGINA
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    st.button("🔄 Regenerar Resposta", on_click=handle_regenerate, use_container_width=True)

if prompt := st.chat_input("Faça uma pergunta...", key="main_chat_input"):
    if st.session_state.get("documentos_processados"):
        handle_response_generation(prompt)
        st.rerun() # Rerun para mostrar a resposta e os botões
    else:
        st.toast("Por favor, carregue e processe alguns documentos primeiro.", icon="📄")

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Gerenciar Conversa")
    # ... (toda a lógica de salvar, carregar, apagar, como na versão anterior) ...
    # ... (esta parte já estava boa, vamos mantê-la) ...
    if st.button("➕ Nova Conversa", use_container_width=True):
        st.session_state.messages, st.session_state.current_chat = [], "Nova Conversa"
        if 'documentos_processados' in st.session_state: del st.session_state['documentos_processados']
        if 'nomes_ficheiros' in st.session_state: del st.session_state['nomes_ficheiros']
        st.rerun()
    chats_salvos = ["Nova Conversa"] + chat_manager.listar_chats_salvos()
    try: current_chat_index = chats_salvos.index(st.session_state.current_chat)
    except ValueError: current_chat_index = 0
    def on_chat_change():
        selected = st.session_state.select_chat_widget
        if selected != "Nova Conversa":
            st.session_state.messages = chat_manager.carregar_chat(selected)
            st.session_state.documentos_processados = True 
        else:
            st.session_state.messages = []
            if 'documentos_processados' in st.session_state: del st.session_state['documentos_processados']
        st.session_state.current_chat = selected
    st.selectbox("Carregar Conversa:", chats_salvos, index=current_chat_index, key='select_chat_widget', on_change=on_chat_change)
    default_save_name = st.session_state.current_chat if st.session_state.current_chat != "Nova Conversa" else ""
    nome_chat_para_renomear = st.text_input("Renomear conversa:", value=default_save_name)
    if st.button("✍️ Renomear", use_container_width=True):
        if nome_chat_para_renomear and st.session_state.current_chat != "Nova Conversa":
            chat_manager.salvar_chat(st.session_state.messages, nome_chat_para_renomear)
            chat_manager.apagar_chat(st.session_state.current_chat)
            st.session_state.current_chat = nome_chat_para_renomear.replace(".json", "")
            st.rerun()
    if st.button("🗑️ Apagar Conversa Atual", use_container_width=True):
        if st.session_state.current_chat != "Nova Conversa":
            if chat_manager.apagar_chat(st.session_state.current_chat):
                st.session_state.current_chat = "Nova Conversa"
                st.rerun()
        else:
            st.warning("Nenhuma conversa salva selecionada.")
    st.divider()

    # SIDEBAR AGRUPADA COM EXPANDERS
    with st.expander("⚙️ Configurações da Sessão", expanded=False):
        st.subheader("Base de Conhecimento")
        def on_vector_store_change():
            if 'vector_store' in st.session_state: del st.session_state['vector_store']
        st.selectbox("Vector Store:", list(vector_stores_config.keys()), key='vector_store_choice', on_change=on_vector_store_change)
        arquivos_pdf = st.file_uploader("Carregar PDFs", type="pdf", accept_multiple_files=True)
        if st.button("Processar Documentos", key="processar_docs"):
            if arquivos_pdf:
                with st.spinner("A processar..."):
                    nomes_ficheiros = [f.name for f in arquivos_pdf]
                    lista_chunks, lista_metadados = [], []
                    for arquivo in arquivos_pdf:
                        texto = "".join(p.extract_text() or "" for p in pypdf.PdfReader(io.BytesIO(arquivo.getvalue())).pages)
                        chunks, metadados = dividir_texto_em_chunks(texto, arquivo.name, st.session_state.get('debug_mode', False))
                        lista_chunks.extend(chunks)
                        lista_metadados.extend(metadados)
                    if lista_chunks: st.session_state.vector_store.adicionar(lista_chunks, lista_metadados)
                    st.session_state.nomes_ficheiros = nomes_ficheiros
                    st.session_state.documentos_processados = True
                st.success("Documentos processados!")
            else:
                st.warning("Nenhum PDF carregado.")
        
        st.divider()
        st.subheader("Configuração do LLM")
        provedor_selecionado = st.selectbox("Provedor de LLM:", list(providers_config.keys()), key="provedor_selecionado")
        config_provedor_atual = providers_config[provedor_selecionado]
        st.write(f"Modelo: `{config_provedor_atual.get('model', '')}`")
        
        def on_api_key_change():
            key = st.session_state[f"api_key_input_{provedor_selecionado}"]
            if key and "SUA_CHAVE" not in key:
                st.session_state.api_keys[provedor_selecionado] = key
                secrets_manager.save_api_key(provedor_selecionado, key)
                st.toast(f"✅ Chave API para {provedor_selecionado} salva!", icon="🔑")

        api_key_input = st.text_input(f"Chave API para {provedor_selecionado}", 
            value=st.session_state.api_keys.get(provedor_selecionado, ''), 
            type="password", 
            key=f"api_key_input_{provedor_selecionado}",
            on_change=on_api_key_change
        )
        st.session_state.debug_mode = st.checkbox("🐛 Modo Debug", value=st.session_state.get('debug_mode', False))

    with st.expander("🤖 Parâmetros de Geração", expanded=False):
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
import streamlit as st
import pypdf
import io

# Importa as funções dos módulos de lógica
from config_loader import carregar_config
from llm_handler import gerar_resposta_com_llm
from rag_processor import dividir_texto_em_chunks, buscar_contexto_relevante
from vector_store_factory import get_vector_store
import chat_manager
import secrets_manager
import profile_manager
from metadata_extractor import extrair_metadados_pdf, filtrar_artigos_por_autor
from researcher_profile import gerar_perfil_pesquisador


# --- LAYOUT E CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="RAG Acadêmico", layout="wide", page_icon="🔬")

# CSS limpo e funcional
st.markdown("""
    <style>
        /* Esconde os ícones padrão do Streamlit nas mensagens */
        .stChatMessage button {
            visibility: hidden;
        }
        
        /* Mostra os botões ao passar o mouse */
        .stChatMessage:hover button {
            visibility: visible;
        }
        
        /* Estilo para botões pequenos e inline */
        div[data-testid="column"] button {
            padding: 0.25rem 0.5rem;
            font-size: 0.875rem;
            min-height: 1.5rem;
            background-color: transparent;
            border: 1px solid rgba(49, 51, 63, 0.2);
            border-radius: 0.25rem;
        }
        
        div[data-testid="column"] button:hover {
            background-color: rgba(151, 166, 195, 0.15);
            border-color: rgba(49, 51, 63, 0.4);
        }
        
        /* Botão regenerar com destaque */
        .regenerate-btn button {
            background-color: #FF4B4B;
            color: white;
            border: none;
            padding: 0.25rem 1rem;
            font-weight: 500;
        }
        
        .regenerate-btn button:hover {
            background-color: #FF6B6B;
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

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
default_states = {
    'temperature': llm_config['temperature'], 
    'top_p': llm_config['top_p'],
    'top_k': llm_config['top_k'], 
    'max_output_tokens': llm_config['max_output_tokens'],
    'vector_store': None, 
    'vector_store_choice': list(vector_stores_config.keys())[0],
    'messages': [], 
    'current_chat': "Nova Conversa", 
    'editing_message_index': None,
    'api_keys': secrets_manager.load_secrets(),
    'lista_metadados_completos': []
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
        with st.spinner("pensando..."):
            resposta = gerar_resposta_com_llm(
                provider_name=provedor, 
                api_key=api_key, 
                model_config=providers_config[provedor],
                contexto=buscar_contexto_relevante(
                    st.session_state.vector_store, 
                    prompt, 
                    st.session_state.get('nomes_ficheiros', [])
                ),
                pergunta=prompt, 
                historico_chat=st.session_state.messages[:-1],
                nomes_ficheiros=st.session_state.get('nomes_ficheiros', []),
                config_geracao={
                    "temperature": st.session_state.temperature, 
                    "top_p": st.session_state.top_p, 
                    "top_k": st.session_state.top_k, 
                    "max_output_tokens": st.session_state.max_output_tokens
                },
                metadados=st.session_state.get("lista_metadados")
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

def delete_message(idx):
    st.session_state.messages.pop(idx)
    chat_manager.salvar_chat(st.session_state.messages, st.session_state.current_chat)
    st.rerun()

def copy_message(content):
    # Você pode usar pyperclip aqui se quiser
    st.toast("Mensagem copiada!", icon="📋")

# --- LAYOUT PRINCIPAL ---
st.title("🔬 UNESPedia LM: Converse com seus Artigos")

# --- ÁREA DO CHAT ---
chat_container = st.container()

with chat_container:
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            # Conteúdo da mensagem
            st.markdown(msg["content"])
            
            # Controles inline (aparecem no hover devido ao CSS)
            cols = st.columns([1, 1, 1, 10])
            
            with cols[0]:
                if st.button("📋", key=f"copy_{idx}", help="Copiar"):
                    copy_message(msg["content"])
            
            with cols[1]:
                if st.button("✏️", key=f"edit_{idx}", help="Editar"):
                    st.session_state.editing_message_index = idx
                    st.rerun()
            
            with cols[2]:
                if st.button("🗑️", key=f"del_{idx}", help="Apagar"):
                    delete_message(idx)
            
            # Botão regenerar (apenas para última mensagem do assistente)
            if msg["role"] == "assistant" and idx == len(st.session_state.messages) - 1:
                with cols[3]:
                    col_spacer, col_regen = st.columns([8, 2])
                    with col_regen:
                        if st.button("🔄 Regenerar", key=f"regen_{idx}", 
                                   use_container_width=True,
                                   help="Regenerar resposta"):
                            handle_regenerate()
                            st.rerun()

# --- CHAT INPUT ---
if prompt := st.chat_input("Faça uma pergunta...", key="main_chat_input"):
    if st.session_state.get("documentos_processados"):
        handle_response_generation(prompt)
        st.rerun()
    else:
        st.toast("Por favor, carregue e processe alguns documentos primeiro.", icon="📄")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Gerenciar Conversa")
    
    if st.button("➕ Nova Conversa", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat = "Nova Conversa"
        if 'documentos_processados' in st.session_state: 
            del st.session_state['documentos_processados']
        if 'nomes_ficheiros' in st.session_state: 
            del st.session_state['nomes_ficheiros']
        st.rerun()
    
    chats_salvos = ["Nova Conversa"] + chat_manager.listar_chats_salvos()
    try: 
        current_chat_index = chats_salvos.index(st.session_state.current_chat)
    except ValueError: 
        current_chat_index = 0
    
    def on_chat_change():
        selected = st.session_state.select_chat_widget
        if selected != "Nova Conversa":
            st.session_state.messages = chat_manager.carregar_chat(selected)
            st.session_state.documentos_processados = True 
        else:
            st.session_state.messages = []
            if 'documentos_processados' in st.session_state: 
                del st.session_state['documentos_processados']
        st.session_state.current_chat = selected
    
    st.selectbox("Carregar Conversa:", chats_salvos, index=current_chat_index, 
                key='select_chat_widget', on_change=on_chat_change)
    
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

    # CONFIGURAÇÕES AGRUPADAS
    with st.expander("⚙️ Configurações da Sessão", expanded=False):
        st.subheader("Base de Conhecimento")
        
        def on_vector_store_change():
            if 'vector_store' in st.session_state: 
                del st.session_state['vector_store']
        
        st.selectbox("Vector Store:", list(vector_stores_config.keys()), 
                    key='vector_store_choice', on_change=on_vector_store_change)
        
        arquivos_pdf = st.file_uploader("Carregar PDFs", type="pdf", accept_multiple_files=True)
        
        if st.button("Processar Documentos", key="processar_docs"):
            if arquivos_pdf:
                with st.spinner("A processar..."):
                    nomes_ficheiros = [f.name for f in arquivos_pdf]
                    lista_chunks, lista_metadados = [], []
                    lista_metadados_completos = []  # ← NOVO

                    for arquivo in arquivos_pdf:
                        # ← NOVO: Extrair metadados
                        pdf_bytes = arquivo.getvalue()
                        
                        metadata_completo = extrair_metadados_pdf(
                            pdf_bytes, arquivo.name
                        )
                        lista_metadados_completos.append(metadata_completo)

                        # Processar texto (código original adaptado)
                        texto = "".join(
                            p.extract_text() or ""
                            for p in pypdf.PdfReader(
                                io.BytesIO(pdf_bytes)
                            ).pages
                        )
                        
                        chunks, metadados = dividir_texto_em_chunks(
                            texto, arquivo.name,
                            st.session_state.get('debug_mode', False)
                        )
                        lista_chunks.extend(chunks)
                        lista_metadados.extend(metadados)

                    if lista_chunks:
                        st.session_state.vector_store.adicionar(
                            lista_chunks, lista_metadados
                        )
                        st.session_state.lista_metadados = lista_metadados
                        st.session_state.lista_metadados_completos = lista_metadados_completos  

                    st.session_state.nomes_ficheiros = nomes_ficheiros
                    st.session_state.documentos_processados = True
                    st.session_state.lista_metadados_completos = lista_metadados_completos  


                st.success("Documentos processados!")

                # ← NOVO: Mostrar metadados extraídos
                if 'lista_metadados_completos' in st.session_state and st.session_state.lista_metadados_completos:
                    with st.expander("📄 Metadados Extraídos", expanded=False):
                        for meta in st.session_state.lista_metadados_completos:
                            st.write(f"**{meta['titulo'][:80]}...**")
                            autores_str = ', '.join(meta['autores'][:3])
                            if len(meta['autores']) > 3:
                                autores_str += f" (e mais {len(meta['autores']) - 3})"
                            st.write(f"- Autores: {autores_str}")
                            if meta['ano']:
                                st.write(f"- Ano: {meta['ano']}")
                            st.write("---")
        
        st.divider()
        st.subheader("Configuração do LLM")
        provedor_selecionado = st.selectbox("Provedor de LLM:", list(providers_config.keys()), 
                                           key="provedor_selecionado")
        config_provedor_atual = providers_config[provedor_selecionado]
        st.write(f"Modelo: `{config_provedor_atual.get('model', '')}`")
        
        def on_api_key_change():
            key = st.session_state[f"api_key_input_{provedor_selecionado}"]
            if key and "SUA_CHAVE" not in key:
                st.session_state.api_keys[provedor_selecionado] = key
                secrets_manager.save_api_key(provedor_selecionado, key)
                st.toast(f"✅ Chave API para {provedor_selecionado} salva!", icon="🔑")

        api_key_input = st.text_input(
            f"Chave API para {provedor_selecionado}", 
            value=st.session_state.api_keys.get(provedor_selecionado, ''), 
            type="password", 
            key=f"api_key_input_{provedor_selecionado}",
            on_change=on_api_key_change
        )
        
        st.session_state.debug_mode = st.checkbox("🐛 Modo Debug", 
                                                 value=st.session_state.get('debug_mode', False))
    
    with st.expander("📚 Perfis Salvos", expanded=False):
        st.subheader("Biblioteca de Pesquisadores")
        
        # Listar todos os perfis
        perfis_disponiveis = profile_manager.listar_perfis_salvos()
        
        if not perfis_disponiveis:
            st.info("📭 Nenhum perfil salvo ainda. Gere um perfil na seção abaixo para começar!")
        else:
            # Barra de pesquisa
            query = st.text_input(
                "🔍 Buscar por nome ou tag:",
                placeholder="Ex: graph learning, recommendation systems",
                key="search_perfis"
            )
            
            # Filtrar perfis
            perfis_filtrados = profile_manager.buscar_perfis(query, perfis_disponiveis)
            
            # Contador
            st.write(f"**{len(perfis_filtrados)}** perfis encontrados")
            
            # Exibir perfis em cards
            for perfil in perfis_filtrados:
                with st.container():
                    # Header do card
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"### 👤 {perfil['nome']}")
                    
                    with col2:
                        if st.button("👁️ Ver", key=f"view_{perfil['filepath']}", use_container_width=True):
                            st.session_state.perfil_visualizando = perfil['filepath']
                    
                    with col3:
                        if st.button("🗑️ Apagar", key=f"del_{perfil['filepath']}", use_container_width=True):
                            if profile_manager.apagar_perfil(perfil['filepath']):
                                st.success("Perfil apagado!")
                                st.rerun()
                    
                    # Metadados
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.caption(f"📅 {perfil['data'][:10]}")
                    with col_b:
                        st.caption(f"📄 {perfil['num_artigos']} artigos")
                    
                    # Tags (mostra até 5 tags principais)
                    if perfil['tags']:
                        tags_display = perfil['tags'][:5]
                        tags_html = " ".join([f'<span style="background-color: #e0e0e0; padding: 2px 8px; border-radius: 10px; font-size: 0.85em; margin-right: 4px;">{tag}</span>' for tag in tags_display])
                        st.markdown(f"🏷️ {tags_html}", unsafe_allow_html=True)
                        
                        # Se tiver mais tags, mostra contador
                        if len(perfil['tags']) > 5:
                            st.caption(f"+ {len(perfil['tags']) - 5} tags")
                    
                    st.divider()
            
            # Modal de visualização (se um perfil foi clicado)
            if 'perfil_visualizando' in st.session_state and st.session_state.perfil_visualizando:
                perfil_completo = profile_manager.carregar_perfil(st.session_state.perfil_visualizando)
                
                if perfil_completo:
                    st.markdown("---")
                    st.markdown(f"## 📊 Perfil Detalhado: {perfil_completo['nome_pesquisador']}")
                    
                    # Botões de ação
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        # Download do perfil completo
                        perfil_md_completo = profile_manager.exportar_perfil_markdown(perfil_completo)
                        st.download_button(
                            label="📥 Baixar Perfil Completo",
                            data=perfil_md_completo,
                            file_name=f"perfil_{perfil_completo['nome_pesquisador'].replace(' ', '_')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    
                    with col2:
                        # Download apenas do texto do perfil
                        st.download_button(
                            label="📄 Baixar Só Perfil",
                            data=perfil_completo['perfil_markdown'],
                            file_name=f"perfil_simples_{perfil_completo['nome_pesquisador'].replace(' ', '_')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    
                    with col3:
                        if st.button("✖️ Fechar", use_container_width=True):
                            del st.session_state.perfil_visualizando
                            st.rerun()
                    
                    # Exibe o perfil
                    st.markdown(perfil_completo['perfil_markdown'])
                    
                    # Seção de tags expandível
                    with st.expander("🏷️ Todas as Tags", expanded=False):
                        tags_html = " ".join([
                            f'<span style="background-color: #4CAF50; color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.9em; margin: 4px; display: inline-block;">{tag}</span>' 
                            for tag in perfil_completo['tags']
                        ])
                        st.markdown(tags_html, unsafe_allow_html=True)
                    
                    # Seção de artigos expandível
                    with st.expander(f"📚 Artigos Analisados ({len(perfil_completo['artigos'])})", expanded=False):
                        for i, artigo in enumerate(perfil_completo['artigos'], 1):
                            st.write(f"**{i}. {artigo['titulo']}**")
                            st.write(f"   - Ano: {artigo['ano'] if artigo['ano'] else 'N/A'}")
                            st.write(f"   - Autores: {', '.join(artigo['autores'][:3])}")
                            if len(artigo['autores']) > 3:
                                st.write(f"     (+ {len(artigo['autores']) - 3} coautores)")
                            st.write("")




    with st.expander("📊 Perfil de Pesquisador", expanded=False):
        st.subheader("Analisar Pesquisador")
        
        # Verifica se há metadados processados
        if 'lista_metadados_completos' not in st.session_state or not st.session_state.lista_metadados_completos:
            st.warning("⚠️ Processe alguns documentos primeiro para gerar perfis de autores.")
        else:
            # ===== COLETA TODOS OS AUTORES ÚNICOS =====
            todos_autores = set()
            for meta in st.session_state.lista_metadados_completos:
                for autor in meta['autores']:
                    todos_autores.add(autor)
            
            lista_autores_unicos = sorted(list(todos_autores))
            
            if not lista_autores_unicos:
                st.warning("⚠️ Nenhum autor foi detectado nos documentos processados.")
            else:
                # ===== SELEÇÃO DO PESQUISADOR =====
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**Opção 1:** Selecione um autor da lista")
                    pesquisador_selecionado = st.selectbox(
                        "Autores encontrados:",
                        options=[""] + lista_autores_unicos,
                        key="select_pesquisador"
                    )
                
                with col2:
                    st.write("**Opção 2:** Digite o nome")
                    pesquisador_digitado = st.text_input(
                        "Nome do pesquisador:",
                        key="input_pesquisador"
                    )
                
                # Decide qual nome usar (prioriza o digitado)
                nome_pesquisador = pesquisador_digitado.strip() if pesquisador_digitado.strip() else pesquisador_selecionado
                
                # ===== FILTRAR ARTIGOS DO PESQUISADOR (ANTES DE GERAR) =====
                artigos_pesquisador = []
                if nome_pesquisador:
                    from metadata_extractor import filtrar_artigos_por_autor
                    
                    artigos_pesquisador = filtrar_artigos_por_autor(
                        st.session_state.lista_metadados_completos,
                        nome_pesquisador,
                        threshold=0.7
                    )
                
                # ===== BOTÃO GERAR PERFIL =====
                if st.button("🔍 Gerar Perfil Completo", type="primary", disabled=not nome_pesquisador):
                    
                    # Verificar se encontrou artigos
                    if not artigos_pesquisador:
                        st.error(f"❌ Nenhum artigo encontrado para '{nome_pesquisador}' (threshold=0.7)")
                    else:
                        # Extrair keywords dos artigos ANTES de gerar perfil
                        from researcher_profile import extrair_palavras_chave_simples
                        keywords_sugeridas = extrair_palavras_chave_simples(artigos_pesquisador)
                        
                        # Importa o módulo de geração de perfil
                        from researcher_profile import gerar_perfil_pesquisador
                        
                        with st.spinner(f"Analisando publicações de {nome_pesquisador}..."):
                            perfil = gerar_perfil_pesquisador(
                                nome_pesquisador=nome_pesquisador,
                                lista_metadados=st.session_state.lista_metadados_completos,
                                vector_store=st.session_state.vector_store,
                                provider_name=st.session_state.provedor_selecionado,
                                api_key=st.session_state.api_keys.get(st.session_state.provedor_selecionado),
                                model_config=providers_config[st.session_state.provedor_selecionado],
                                config_geracao={
                                    "temperature": 0.3,
                                    "top_p": 0.95,
                                    "top_k": 40,
                                    "max_output_tokens": 3000
                                }
                            )
                        
                        # Mostra o perfil
                        st.markdown(f"## 📊 Perfil: {nome_pesquisador}")
                        st.markdown(perfil)
                        
                        # ===== SALVAR PERFIL AUTOMATICAMENTE =====
                        try:
                            import profile_manager
                            filepath_salvo = profile_manager.salvar_perfil(
                                nome_pesquisador=nome_pesquisador,
                                perfil_texto=perfil,
                                artigos=artigos_pesquisador,  # ← AGORA ESTÁ DEFINIDA!
                                keywords_artigos=keywords_sugeridas
                            )
                            st.success(f"✅ Perfil salvo automaticamente!")
                            
                            # Botão para ver na biblioteca
                            if st.button("📚 Ver na Biblioteca de Perfis"):
                                st.session_state.perfil_visualizando = filepath_salvo
                                st.rerun()
                        except Exception as e:
                            st.warning(f"⚠️ Não foi possível salvar o perfil: {e}")
                        
                        # Botão de download
                        st.download_button(
                            label="📥 Baixar Perfil (Markdown)",
                            data=perfil,
                            file_name=f"perfil_{nome_pesquisador.replace(' ', '_')}.md",
                            mime="text/markdown"
                        )
                
                # ===== MOSTRAR ARTIGOS DO PESQUISADOR =====
                if nome_pesquisador and artigos_pesquisador:
                    with st.expander(f"📚 Artigos de {nome_pesquisador} ({len(artigos_pesquisador)} encontrados)", expanded=False):
                        for i, meta in enumerate(artigos_pesquisador, 1):
                            st.write(f"**{i}. {meta['titulo']}**")
                            st.write(f"   - Autores: {', '.join(meta['autores'])}")
                            st.write(f"   - Ano: {meta['ano'] if meta['ano'] else 'N/A'}")
                            
                            # Encontrar posição do pesquisador
                            try:
                                posicao = next(
                                    idx for idx, autor in enumerate(meta['autores'])
                                    if nome_pesquisador.lower() in autor.lower()
                                )
                                if posicao == 0:
                                    st.write(f"   - Posição: 1º autor (primeiro autor)")
                                else:
                                    st.write(f"   - Posição: {posicao + 1}º autor")
                            except StopIteration:
                                st.write(f"   - Posição: Coautor")
                            
                            st.write("")





    with st.expander("🤖 Parâmetros de Geração", expanded=False):
        st.write("**Presets**")
        cols = st.columns(len(presets_config))
        for i, (p_name, p_values) in enumerate(presets_config.items()):
            if cols[i].button(p_name, use_container_width=True, key=f"preset_{i}"):
                st.session_state.temperature = p_values['temperature']
                st.session_state.top_p = p_values['top_p']
                st.session_state.top_k = p_values['top_k']
                st.rerun()
        
        st.divider()
        st.slider("Temperature", 0.0, 2.0, key='temperature', step=0.1)
        st.slider("Top-p", 0.0, 1.0, key='top_p', step=0.05)
        st.slider("Top-k", 1, 100, key='top_k', step=1)
        st.slider("Max Output Tokens", 100, 8000, key='max_output_tokens', step=100)
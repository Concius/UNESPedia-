# chat_manager.py

import os
import json
import streamlit as st
from datetime import datetime

# Define o diretório onde os chats serão guardados
CHAT_HISTORY_DIR = "chats"

def inicializar_diretorio_chats():
    """Garante que o diretório de chats existe."""
    if not os.path.exists(CHAT_HISTORY_DIR):
        os.makedirs(CHAT_HISTORY_DIR)

def listar_chats_salvos():
    """Retorna uma lista de todos os ficheiros de chat salvos."""
    inicializar_diretorio_chats()
    # Filtra para mostrar apenas ficheiros .json e remove a extensão para a UI
    files = [f.replace(".json", "") for f in os.listdir(CHAT_HISTORY_DIR) if f.endswith(".json")]
    files.sort(reverse=True) # Mostra os mais recentes primeiro
    return files

def salvar_chat(historico_mensagens, nome_arquivo):
    """Salva o histórico de mensagens num ficheiro JSON."""
    inicializar_diretorio_chats()
    
    # Adiciona a extensão .json se não existir
    if not nome_arquivo.endswith(".json"):
        nome_arquivo += ".json"
        
    filepath = os.path.join(CHAT_HISTORY_DIR, nome_arquivo)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(historico_mensagens, f, ensure_ascii=False, indent=4)
        st.toast(f"Conversa salva em '{nome_arquivo}'!", icon="💾")
        return True
    except Exception as e:
        st.error(f"Erro ao salvar a conversa: {e}")
        return False

def carregar_chat(nome_arquivo):
    """Carrega o histórico de mensagens de um ficheiro JSON."""
    inicializar_diretorio_chats()

    if not nome_arquivo.endswith(".json"):
        nome_arquivo += ".json"
        
    filepath = os.path.join(CHAT_HISTORY_DIR, nome_arquivo)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            historico = json.load(f)
            st.toast(f"Conversa '{nome_arquivo}' carregada.", icon="📂")
            return historico
    except FileNotFoundError:
        st.error(f"Ficheiro de conversa '{nome_arquivo}' não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar a conversa: {e}")
        return None

def apagar_chat(nome_arquivo):
    """Apaga um ficheiro de chat salvo."""
    inicializar_diretorio_chats()

    if not nome_arquivo.endswith(".json"):
        nome_arquivo += ".json"
        
    filepath = os.path.join(CHAT_HISTORY_DIR, nome_arquivo)
    
    try:
        os.remove(filepath)
        st.toast(f"Conversa '{nome_arquivo}' apagada!", icon="🗑️")
        return True
    except FileNotFoundError:
        st.error(f"Não foi possível apagar: ficheiro '{nome_arquivo}' não encontrado.")
        return False
    except Exception as e:
        st.error(f"Erro ao apagar a conversa: {e}")
        return False

def gerar_nome_chat_padrao():
    """Gera um nome de ficheiro padrão com base na data e hora atuais."""
    return f"chat_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
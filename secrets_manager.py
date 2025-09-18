# secrets_manager.py
import json
import os
import streamlit as st

import os, pathlib
SECRETS_DIR  = pathlib.Path.home() / ".unespedia"
SECRETS_FILE = SECRETS_DIR / "secrets.json"
SECRETS_DIR.mkdir(exist_ok=True)   # ← add this line

def load_secrets():
    """Carrega os segredos do ficheiro JSON."""
    if os.path.exists(SECRETS_FILE):
        try:
            with open(SECRETS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_secrets(secrets_dict):
    """Salva o dicionário de segredos no ficheiro JSON."""
    try:
        with open(SECRETS_FILE, 'w') as f:
            json.dump(secrets_dict, f, indent=4)
    except Exception as e:
        st.error(f"Não foi possível salvar os segredos: {e}")

def get_api_key(provider_name):
    """Obtém a chave de API para um provedor específico."""
    secrets = load_secrets()
    return secrets.get(provider_name)

def save_api_key(provider_name, api_key):
    """Salva a chave de API para um provedor específico."""
    secrets = load_secrets()
    secrets[provider_name] = api_key
    save_secrets(secrets)
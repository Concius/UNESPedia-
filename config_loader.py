# config_loader.py

import yaml
import streamlit as st

@st.cache_data
def carregar_config():
    """Carrega as configurações do arquivo config.yaml."""
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            return config
    except FileNotFoundError:
        st.error("Erro: O arquivo 'config.yaml' não foi encontrado. Certifique-se de que ele existe no diretório principal.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo de configuração: {e}")
        return None
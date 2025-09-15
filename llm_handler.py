# llm_handler.py

from llm_factory import get_llm_provider

def gerar_resposta_com_llm(provider_name, api_key, model_config, contexto, pergunta, historico_chat, nomes_ficheiros, config_geracao):
    """
    Obtém o provedor de LLM correto e solicita a geração da resposta.
    """
    try:
        # 1. Usa a fábrica para obter a instância do provedor
        provedor = get_llm_provider(provider_name, api_key, model_config)
        
        # 2. Chama o método padronizado para gerar a resposta
        resposta = provedor.gerar_resposta(
            contexto=contexto,
            pergunta=pergunta,
            historico_chat=historico_chat,
            nomes_ficheiros=nomes_ficheiros,
            config_geracao=config_geracao
        )
        return resposta
        
    except Exception as e:
        return f"Ocorreu um erro no handler do LLM: {e}"
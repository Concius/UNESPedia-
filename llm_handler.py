# llm_handler.py

from llm_factory import get_llm_provider


def gerar_resposta_com_llm(provider_name, api_key, model_config, contexto, pergunta,
                          historico_chat, nomes_ficheiros, config_geracao, metadados=None):
    """
    Obtém o provedor de LLM correto e solicita a geração da resposta.
    Se 'metadados' for fornecido, injeta citações (página/secão) em cada chunk do contexto.
    """
    try:
        # 1. Injeta citações no contexto (caso haja metadados)
        if metadados:
            # Quebra o contexto nos blocos separados por "---"
            blocos = contexto.split("\n---\n")
            if len(blocos) == len(metadados):          # segurança: mesma quantidade
                blocos_citados = []
                for texto, meta in zip(blocos, metadados):
                    cit = f"(Fonte: {meta['fonte']}, p. {meta['page']}, sec. {meta['section']})"
                    blocos_citados.append(f"{texto.strip()} {cit}")
                contexto = "\n---\n".join(blocos_citados)

        # 2. Fábrica de provedores
        provedor = get_llm_provider(provider_name, api_key, model_config)

        # 3. Geração da resposta
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
# llm_providers/claude.py

import anthropic
from .base import LLMProvider

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key, model_name='claude-sonnet-4-20250514'):
        self.api_key = api_key
        self.model_name = model_name
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def gerar_resposta(self, contexto, pergunta, historico_chat, nomes_ficheiros, config_geracao):
        # Claude também prefere um prompt de sistema e um histórico de mensagens
        prompt_sistema = f"""
        **Instruções:** Você é um assistente de pesquisa. Responda à última pergunta do usuário baseando-se no "Contexto" fornecido e no "Histórico da Conversa".
        Os ficheiros carregados pelo usuário são: {', '.join(nomes_ficheiros)}.
        O contexto relevante extraído dos documentos é:\n---\n{contexto}\n---
        """

        # Adapta o histórico, garantindo que começa com 'user'
        mensagens = []
        for msg in historico_chat:
            # Garante a alternância correta de roles
            if not mensagens or mensagens[-1]["role"] != msg["role"]:
                 mensagens.append({"role": msg["role"], "content": msg["content"]})
        
        # Adiciona a pergunta atual
        if not mensagens or mensagens[-1]["role"] == "assistant":
            mensagens.append({"role": "user", "content": pergunta})
        else: # Se a última mensagem já for do usuário, anexa a pergunta
            mensagens[-1]["content"] += f"\n\n{pergunta}"


        try:
            resposta = self.client.messages.create(
                model=self.model_name,
                system=prompt_sistema,
                messages=mensagens,
                temperature=config_geracao.get('temperature'),
                top_p=config_geracao.get('top_p'),
                max_tokens=config_geracao.get('max_output_tokens'),
            )
            return resposta.content[0].text
        except Exception as e:
            return f"Erro ao chamar a API do Claude: {e}"
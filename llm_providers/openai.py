# llm_providers/openai.py

import openai
from .base import LLMProvider

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key, model_name, api_base_url=None):
        self.api_key = api_key
        self.model_name = model_name
        self.api_base_url = api_base_url
        
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.api_base_url  # Será None para a OpenAI oficial
        )

    def gerar_resposta(self, contexto, pergunta, historico_chat, nomes_ficheiros, config_geracao):
        # Para APIs do tipo OpenAI, é melhor enviar o histórico como uma lista de mensagens
        # e o prompt do sistema separadamente.
        
        prompt_sistema = f"""
        **Instruções:** Você é um assistente de pesquisa. Responda à última pergunta do usuário baseando-se no "Contexto" fornecido e no "Histórico da Conversa".
        Os ficheiros carregados pelo usuário são: {', '.join(nomes_ficheiros)}.
        O contexto relevante extraído dos documentos é:\n---\n{contexto}\n---
        """
        
        mensagens = [{"role": "system", "content": prompt_sistema}]
        
        # Adapta o histórico para o formato do OpenAI
        for msg in historico_chat:
            mensagens.append({"role": msg["role"], "content": msg["content"]})
            
        mensagens.append({"role": "user", "content": pergunta})

        try:
            resposta = self.client.chat.completions.create(
                model=self.model_name,
                messages=mensagens,
                temperature=config_geracao.get('temperature'),
                top_p=config_geracao.get('top_p'),
                max_tokens=config_geracao.get('max_output_tokens'),
            )
            return resposta.choices[0].message.content
        except Exception as e:
            return f"Erro ao chamar a API ({self.model_name}): {e}"
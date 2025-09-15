# llm_providers/gemini.py

import google.generativeai as genai
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self, api_key, model_name='gemini-1.5-flash'):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=self.api_key)

    def gerar_resposta(self, contexto, pergunta, historico_chat, nomes_ficheiros, config_geracao):
        prompt = self._construir_prompt(contexto, pergunta, historico_chat, nomes_ficheiros)
        
        generation_config = genai.types.GenerationConfig(
            temperature=config_geracao.get('temperature'),
            top_p=config_geracao.get('top_p'),
            top_k=config_geracao.get('top_k'),
            max_output_tokens=config_geracao.get('max_output_tokens'),
        )
        
        model = genai.GenerativeModel(self.model_name, generation_config=generation_config)
        
        try:
            resposta = model.generate_content(prompt)
            return resposta.text
        except Exception as e:
            return f"Erro ao chamar a API do Gemini: {e}"
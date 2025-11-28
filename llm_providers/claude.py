# llm_providers/claude.py

import anthropic
from .base import LLMProvider

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key, model_name='claude-sonnet-4-20250514'):
        self.api_key = api_key
        self.model_name = model_name
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def gerar_resposta(self, contexto, pergunta, historico_chat, nomes_ficheiros, config_geracao,
                      system_prompt=None, persona_prompt=None):
        # Claude também prefere um prompt de sistema e um histórico de mensagens
        # Usar system_prompt customizado se fornecido
        if system_prompt is None:
            system_prompt = """Você é um assistente de pesquisa acadêmica. Responda à última pergunta do usuário baseando-se no "Contexto" fornecido.

IMPORTANTE: sempre que usar informações do contexto, cite a fonte exatamente como: (Fonte, p. {page}, sec. {section})."""
        
        # Adicionar persona se fornecida
        persona_section = ""
        if persona_prompt is not None:
            persona_section = f"\n\n**PERSONA ATIVA:**\n{persona_prompt}\n"
        
        # Montar prompt_sistema final
        prompt_sistema = f"""{system_prompt}{persona_section}

**Arquivos carregados:** {', '.join(nomes_ficheiros)}

**Contexto relevante:**
---
{contexto}
---"""

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
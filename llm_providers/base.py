# llm_providers/base.py

from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """
    Classe base abstrata para provedores de LLM.
    Define a interface que todos os provedores devem implementar.
    """

    @abstractmethod
    def gerar_resposta(self, contexto, pergunta, historico_chat, nomes_ficheiros, config_geracao):
        """
        Gera uma resposta baseada no prompt.

        Args:
            contexto (str): O contexto extraído dos documentos (RAG).
            pergunta (str): A última pergunta do usuário.
            historico_chat (list): Uma lista de dicionários representando o histórico da conversa.
            nomes_ficheiros (list): Lista de nomes de arquivos carregados.
            config_geracao (dict): Dicionário com parâmetros como 'temperature', 'top_p', etc.

        Returns:
            str: A resposta gerada pelo modelo.
        """
        pass

    def _construir_prompt(self, contexto, pergunta, historico_chat, nomes_ficheiros):
        """
        Método auxiliar para construir o prompt final.
        Pode ser sobrescrito se um provedor precisar de um formato de prompt diferente.
        """
        historico_formatado = "\n".join([f"{msg['role']}: {msg['content']}" for msg in historico_chat])

        prompt = f"""
        **Instruções:** Você é um assistente de pesquisa. Responda à "Última pergunta do usuário" baseando-se no "Contexto" e no "Histórico da Conversa".
        Os ficheiros carregados pelo usuário são: {', '.join(nomes_ficheiros)}.

        **Histórico da Conversa:**
        {historico_formatado}

        **Contexto extraído dos documentos (use para basear a sua resposta):**
        ---
        {contexto}
        ---

        **Última pergunta do usuário:** {pergunta}

        **Sua Resposta:**
        """
        return prompt
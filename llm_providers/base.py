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
        Constrói o prompt final com instruções de citação.
        """
        historico_formatado = "\n".join([f"{msg['role']}: {msg['content']}" for msg in historico_chat])

        # --- nova instrução de citação ---
        citacao_instrucao = (
            "IMPORTANTE: sempre que usar informações do contexto, "
            "cite a fonte exatamente como: (Fonte, p. {page}, sec. {section}). "
            "Se a página ou seção não estiver disponível, omita esse campo."
        )

        prompt = f"""
        Você é um assistente de pesquisa acadêmica. Responda à **Última pergunta do usuário** baseando-se **apenas** no **Contexto** e no **Histórico da Conversa**.

        {citacao_instrucao}

        Arquivos carregados: {', '.join(nomes_ficheiros)}.

        **Histórico da Conversa:**
        {historico_formatado}

        **Contexto (cada trecho já inclui página/seção):**
        ---
        {contexto}
        ---

        **Última pergunta do usuário:** {pergunta}

        **Sua resposta (em português, com citações):**
        """
        return prompt
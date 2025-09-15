# vector_stores/base.py

from abc import ABC, abstractmethod

class VectorStore(ABC):
    """
    Classe base abstrata para provedores de Vector Store.
    Define a interface que todos os provedores devem implementar.
    """

    @abstractmethod
    def carregar_ou_criar(self, chunks, metadados):
        """
        Carrega a base de dados vetorial se já existir, ou cria uma nova
        com os chunks e metadados fornecidos.
        """
        pass

    @abstractmethod
    def adicionar(self, chunks, metadados):
        """
        Adiciona novos chunks e metadados a uma base de dados existente.
        """
        pass

    @abstractmethod
    def buscar(self, query_text, n_results, where=None):
        """
        Realiza uma busca por similaridade na base de dados vetorial.

        Args:
            query_text (str): O texto da pergunta a ser buscada.
            n_results (int): O número de resultados a serem retornados.
            where (dict, optional): Um filtro para metadados (se suportado).

        Returns:
            dict: Um dicionário contendo os documentos e metadados encontrados.
        """
        pass
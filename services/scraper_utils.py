"""
Scraper Utilities Module

Este módulo contém funções utilitárias e helpers para o web scraper,
incluindo operações de rede, manipulação de dados e funções auxiliares.
"""

import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
from typing import Dict, Optional, Tuple


class ScraperUtils:
    """
    Classe com funções utilitárias para operações de scraping,
    manipulação de dados e helpers gerais.
    """

    @staticmethod
    def extract_soup_from_url(url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
        """
        Faz uma requisição HTTP para a URL fornecida e retorna um objeto BeautifulSoup.
        
        Args:
            url (str): A URL da página web a ser requisitada
            timeout (int): Timeout para a requisição em segundos
            
        Returns:
            BeautifulSoup: Objeto BeautifulSoup contendo o conteúdo HTML da página,
                          ou None se a requisição falhar
        """
        try:
            response = requests.get(url, timeout=timeout)
            response.encoding = response.apparent_encoding
            
            if response.status_code == 200:
                html_content = response.text
                return BeautifulSoup(html_content, 'html.parser')
            else:
                print(f"Erro HTTP {response.status_code} ao acessar {url}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar a URL {url}: {e}")
            return None

    @staticmethod
    def extract_and_remove_dict_value(dictionary: Dict, value) -> Optional[str]:
        """
        Extrai o valor de um dicionário e remove a chave/valor do dicionário.
        
        Args:
            dictionary (dict): O dicionário de onde extrair o valor
            value: O valor a ser extraído
            
        Returns:
            str: A chave correspondente ao valor, ou None se não encontrado
        """
        for key in list(dictionary.keys()):
            if dictionary[key] == value:
                del dictionary[key]
                return key
        return None

    @staticmethod
    def save_dataframe_to_csv(dataframe: pd.DataFrame, file_path: str) -> bool:
        """
        Salva um DataFrame em arquivo CSV, criando diretórios se necessário.
        
        Args:
            dataframe (pd.DataFrame): DataFrame a ser salvo
            file_path (str): Caminho do arquivo CSV
            
        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        try:
            # Cria diretórios se não existirem
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Salva o DataFrame
            dataframe.to_csv(file_path, index=False)
            return True
            
        except Exception as e:
            print(f"Erro ao salvar arquivo CSV {file_path}: {e}")
            return False

    @staticmethod
    def load_dataframe_from_csv(file_path: str) -> Optional[pd.DataFrame]:
        """
        Carrega um DataFrame de um arquivo CSV.
        
        Args:
            file_path (str): Caminho do arquivo CSV
            
        Returns:
            pd.DataFrame: DataFrame carregado, ou None se arquivo não existir
        """
        try:
            if os.path.exists(file_path):
                return pd.read_csv(file_path)
            else:
                return None
                
        except Exception as e:
            print(f"Erro ao carregar arquivo CSV {file_path}: {e}")
            return None

    @staticmethod
    def delete_file_if_exists(file_path: str) -> bool:
        """
        Deleta um arquivo se ele existir.
        
        Args:
            file_path (str): Caminho do arquivo a ser deletado
            
        Returns:
            bool: True se deletou ou arquivo não existia, False se houve erro
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
            
        except Exception as e:
            print(f"Erro ao deletar arquivo {file_path}: {e}")
            return False

    @staticmethod
    def extract_books_from_page(url: str, book_dict: Dict, html_parser) -> Tuple[Dict, Optional[str]]:
        """
        Extrai os links dos livros de uma página e retorna o dicionário atualizado
        e o link da próxima página.
        
        Args:
            url (str): URL da página a ser analisada
            book_dict (dict): Dicionário atual de links de livros
            html_parser: Instância do HTMLParser para extrair links
            
        Returns:
            tuple: (Dicionário atualizado de links de livros, URL da próxima página ou None)
        """
        try:
            soup_books = ScraperUtils.extract_soup_from_url(url)
            if soup_books is None:
                return book_dict, None

            soup_books_section = soup_books.find('section')
            if soup_books_section is None:
                return book_dict, None

            # Extrai URLs da página atual
            books_url_current_page = html_parser.extract_links_from_page(
                soup_books_section, url, remove_empty_names=True
            )

            # Remove links de navegação
            link_next = ScraperUtils.extract_and_remove_dict_value(books_url_current_page, 'next')
            link_previous = ScraperUtils.extract_and_remove_dict_value(books_url_current_page, 'previous')

            # Atualiza dicionário de livros
            book_dict.update(books_url_current_page)
            
            return book_dict, link_next

        except Exception as e:
            print(f"Erro ao extrair livros da página {url}: {e}")
            return book_dict, None

    @staticmethod
    def extract_all_books_urls(base_url: str, html_parser, scraping_state=None) -> Dict[str, str]:
        """
        Obtém as URLs de todos os livros navegando por todas as páginas.
        
        Args:
            base_url (str): URL base do site
            html_parser: Instância do HTMLParser
            scraping_state: Estado do scraping para atualização em tempo real (opcional)
            
        Returns:
            dict: Dicionário com URLs dos livros como chaves e títulos como valores
        """
        try:
            # Realiza a leitura da página principal
            soup_principal = ScraperUtils.extract_soup_from_url(base_url)
            if soup_principal is None:
                return {}

            # Extrai links da página principal
            main_page_urls = html_parser.extract_links_from_page(
                soup_principal, base_url, remove_empty_names=True
            )
            
            # Localiza a URL para a página dos livros
            books_page_url = ScraperUtils.extract_and_remove_dict_value(main_page_urls, "Books")
            if books_page_url is None:
                return {}

            # Inicia o dicionário de URLs de livros
            books_url_dict = {}
            current_url = books_page_url
            
            max_pages = 1000  # Limite máximo de páginas (segurança)
            page_count = 0

            # Loop para extrair links de todas as páginas
            while current_url is not None and page_count < max_pages:
             
                page_count += 1
                
                # Extrai livros da página atual
                books_url_dict, current_url = ScraperUtils.extract_books_from_page(
                    current_url, books_url_dict, html_parser
                )
                
                # Atualiza o estado em tempo real se fornecido
                if scraping_state is not None:
                    scraping_state.qtd_books_urls = len(books_url_dict)
                
                # Log de progresso a cada 10 páginas
                if page_count % 10 == 0:    
                    print(f"Processadas {page_count} páginas, {len(books_url_dict)} livros encontrados...")
            
            # Log final
            if page_count >= max_pages:
                print(f"Aviso: Atingido limite máximo de {max_pages} páginas")
            
            # Atualização final do estado
            if scraping_state is not None:
                scraping_state.qtd_books_urls = len(books_url_dict)
            
            print(f"Scraping concluído: {page_count} páginas processadas, {len(books_url_dict)} livros encontrados")

            return books_url_dict

        except Exception as e:
            print(f"Erro ao obter URLs dos livros: {e}")
            return {}

    @staticmethod
    def search_books_in_dataframe(dataframe: pd.DataFrame, title: str = None, category: str = None) -> list:
        """
        Pesquisa livros no DataFrame com base no título e/ou categoria.
        
        Args:
            dataframe (pd.DataFrame): DataFrame com dados dos livros
            title (str, optional): Título do livro para pesquisa
            category (str, optional): Categoria do livro para pesquisa
            
        Returns:
            list: Lista de dicionários contendo os dados dos livros encontrados
        """
        try:
            results = dataframe.copy()

            if title:
                results = results[results['title'].str.contains(title, case=False, na=False)]

            if category:
                results = results[results['category'].str.contains(category, case=False, na=False)]

            return results.to_dict(orient='records')
            
        except Exception as e:
            print(f"Erro ao pesquisar livros: {e}")
            return []

    @staticmethod
    def extract_books_titles_from_dataframe(dataframe: pd.DataFrame) -> list:
        """
        Extrai apenas os títulos dos livros do DataFrame.
        
        Args:
            dataframe (pd.DataFrame): DataFrame com dados dos livros
            
        Returns:
            list: Lista com os títulos dos livros
        """
        try:
            if 'title' in dataframe.columns:
                return dataframe['title'].tolist()
            else:
                return []
                
        except Exception as e:
            print(f"Erro ao extrair títulos: {e}")
            return []

    @staticmethod
    def calculate_scraping_progress(current_count: int, total_count: int) -> float:
        """
        Calcula a porcentagem de progresso do scraping.
        
        Args:
            current_count (int): Número atual de itens processados
            total_count (int): Número total de itens a processar
            
        Returns:
            float: Porcentagem de progresso (0-100)
        """
        if total_count <= 0:
            return 0.0
        
        return min((current_count / total_count) * 100, 100.0)
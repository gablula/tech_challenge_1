"""
Web Scraper Module

Este módulo contém a classe principal WebScraper que orquestra o processo de scraping
utilizando os módulos especializados HTMLParser e ScraperUtils.
"""

from dataclasses import dataclass, field
import pandas as pd
from typing import List, Optional

from .html_parser import HTMLParser
from .scraper_utils import ScraperUtils


@dataclass
class ScrapingState:
    """Estado do processo de scraping."""
    books_dataframe: pd.DataFrame = field(default_factory=pd.DataFrame)
    qtd_books_urls: int = 0
    status: str = "Idle"


class WebScraper:
    """
    Classe principal para web scraping do site Books to Scrape.
    Utiliza HTMLParser para parsing e ScraperUtils para utilitários.
    """
    
    BASE_URL = 'https://books.toscrape.com/'
    SCRAPING_DATABASE_FILE = './data/scraping_books_database.csv'
    
    def __init__(self):
        """Inicializa o scraper com parser HTML e estado."""
        self.state = ScrapingState()
        self.html_parser = HTMLParser()
        self.utils = ScraperUtils()
        self.load_existing_data()
    
    def load_existing_data(self) -> ScrapingState:
        """
        Carrega dados existentes do arquivo CSV se disponível.
        
        Returns:
            ScrapingState: Estado atual do scraping
        """
        existing_data = self.utils.load_dataframe_from_csv(self.SCRAPING_DATABASE_FILE)
        
        if existing_data is not None and len(existing_data) > 0:
            self.state.books_dataframe = existing_data
            self.state.status = "Done"
            self.state.qtd_books_urls = len(existing_data)
            
        return self.state

    def get_status_message(self) -> str:
        """
        Retorna uma mensagem de status para o processo de web scraping.
        
        Returns:
            str: Mensagem indicando o estado atual do processo de scraping
        """
        if self.state.status == "Extracting_urls":
            return f"Scraping em andamento: Extraindo URLs dos livros do site. Aguarde... ({self.state.qtd_books_urls} URLs encontradas até agora)"
            
        elif self.state.status == "Scraping_books":
            if self.state.qtd_books_urls > 0:
                current_count = len(self.state.books_dataframe)
                progress = self.utils.calculate_scraping_progress(current_count, self.state.qtd_books_urls)
                return f"Coletando dados dos livros: {current_count}/{self.state.qtd_books_urls} ({progress:.1f}%). Aguarde a conclusão para acessar as funções de consulta."
            else:
                return "Iniciando coleta de dados dos livros. Aguarde..."
                
        
                
        elif self.state.status == "Done":
            return f"Scraping concluído com sucesso! {self.state.qtd_books_urls} livros coletados e disponíveis para consulta."
        elif self.state.status == "Stopping":
            return "Parando o scraping..."
        elif self.state.status == "Error":
            return "Erro durante o scraping. Use /api/v1/scraper/reset para resetar e tente novamente."
        else:
            return "Scraping não foi iniciado ainda. Use /api/v1/scraper/start para iniciar a coleta de dados."

    def scraper_task(self) -> Optional[pd.DataFrame]:
        """
        Executa a task principal de scraping dos livros.
        
        Returns:
            pd.DataFrame: DataFrame contendo os dados dos livros coletados
        """
        try:
            # Inicializa o processo - Status: Extraindo URLs
            self.state.status = "Extracting_urls"
            self.state.books_dataframe = pd.DataFrame()
            self.state.qtd_books_urls = 0
            
            # Obtém URLs de todos os livros (passa o estado para atualização em tempo real)
            books_urls = self.utils.extract_all_books_urls(self.BASE_URL, self.html_parser, self.state)
            
            if not books_urls:
                self.state.status = "Error"
                return None
            
            # Atualiza status para scraping (qtd_books_urls já foi atualizado durante a extração)
            self.state.status = "Scraping_books"
            books_data_list = []
            
            # Processa cada livro
            for index, book_url in enumerate(books_urls.keys()):
                # Verifica se deve parar
                if self.state.status == "Stopping":
                    self.state.status = "Idle"
                    return None
                
                # Extrai dados do livro
                book_data = self._extract_single_book_data(book_url, index)
                if book_data:
                    books_data_list.append(book_data)
                    
                # Atualiza o DataFrame temporariamente para mostrar progresso
                self.state.books_dataframe = pd.DataFrame(books_data_list)
            
            # Finaliza o processo
            self.state.books_dataframe = pd.DataFrame(books_data_list)
            self.state.qtd_books_urls = len(self.state.books_dataframe)
            self.state.status = "Done"
            
            # Salva os dados
            success = self.utils.save_dataframe_to_csv(
                self.state.books_dataframe, 
                self.SCRAPING_DATABASE_FILE
            )
            
            if not success:
                print("Aviso: Erro ao salvar dados em CSV, mas scraping foi concluído.")
            
            return self.state.books_dataframe
            
        except Exception as e:
            print(f"Erro durante o scraping: {e}")
            self.state.status = "Error"
            return None

    def _extract_single_book_data(self, book_url: str, index: int) -> Optional[dict]:
        """
        Extrai dados de um único livro.
        
        Args:
            book_url (str): URL da página do livro
            index (int): Índice do livro na lista
            
        Returns:
            dict: Dados do livro ou None se houver erro
        """
        try:
            soup = self.utils.extract_soup_from_url(book_url)
            if soup is None:
                return None
            
            return self.html_parser.extract_book_data_complete(soup, book_url, index)
            
        except Exception as e:
            print(f"Erro ao extrair dados do livro {book_url}: {e}")
            return None

    def delete_database(self) -> bool:
        """
        Deleta o arquivo de banco de dados CSV.
        
        Returns:
            bool: True se deletou com sucesso, False caso contrário
        """
        success = self.utils.delete_file_if_exists(self.SCRAPING_DATABASE_FILE)
        
        if success:
            # Reset do estado
            self.state.books_dataframe = pd.DataFrame()
            self.state.qtd_books_urls = 0
            if self.state.status != "Running":
                self.state.status = "Idle"
                
        return success

    def search_books(self, title: str = None, category: str = None) -> List[dict]:
        """
        Pesquisa livros no DataFrame com base no título e/ou categoria.
        
        Args:
            title (str, optional): Título do livro para pesquisa
            category (str, optional): Categoria do livro para pesquisa
            
        Returns:
            List[dict]: Lista de dicionários contendo os dados dos livros encontrados
        """
        return self.utils.search_books_in_dataframe(
            self.state.books_dataframe, 
            title=title, 
            category=category
        )

    def get_book_titles(self) -> List[str]:
        """
        Retorna lista com todos os títulos dos livros.
        
        Returns:
            List[str]: Lista com os títulos dos livros
        """
        return self.utils.extract_books_titles_from_dataframe(self.state.books_dataframe)

    def stop_scraping(self) -> None:
        """
        Sinaliza para parar o processo de scraping.
        """
        if self.state.status == "Running":
            self.state.status = "Stopping"

    def reset_scraping(self) -> bool:
        """
        Para o processo de scraping (se estiver rodando) e limpa os dados.
        
        Returns:
            bool: True se resetou com sucesso
        """
        # Para o scraping se estiver rodando
        if self.state.status == "Running":
            self.stop_scraping()
            # Aguarda até parar (em implementação real, seria melhor usar threading)
            while self.state.status == "Stopping":
                pass
        
        # Limpa os dados
        success = self.delete_database()
        
        if success:
            self.state.status = "Idle"
            
        return success

    def get_scraping_stats(self) -> dict:
        """
        Retorna estatísticas do scraping.
        
        Returns:
            dict: Estatísticas do processo de scraping
        """
        return {
            "status": self.state.status,
            "total_books": self.state.qtd_books_urls,
            "books_in_dataframe": len(self.state.books_dataframe),
            "database_file": self.SCRAPING_DATABASE_FILE,
            "base_url": self.BASE_URL
        }
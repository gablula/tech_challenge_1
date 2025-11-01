"""
HTML Parser Module

Este módulo contém todas as funções responsáveis por fazer parsing e extrair dados
das páginas HTML usando BeautifulSoup. Separado para manter as responsabilidades
de parsing independentes da lógica de controle do scraper.
"""

from bs4 import BeautifulSoup
from urllib.parse import urljoin


class HTMLParser:
    """
    Classe responsável por todas as operações de parsing HTML e extração de dados
    das páginas do Books to Scrape usando BeautifulSoup.
    """
    
    def __init__(self, class_category="breadcrumb", category_link_number=3):
        """
        Inicializa o parser com configurações para extração de categorias.
        
        Args:
            class_category (str): Classe CSS para localizar breadcrumbs de categoria
            category_link_number (int): Número do link da categoria no breadcrumb
        """
        self.class_category = class_category
        self.category_link_number = category_link_number

    def extract_title(self, soup):
        """
        Extrai o título do livro a partir do objeto BeautifulSoup.
        
        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup da página do livro
            
        Returns:
            str: Título do livro
        """
        title_li = soup.find("li", class_="active")
        if title_li:
            return title_li.get_text(strip=True)
        return ""

    def extract_category(self, soup):
        """
        Extrai a categoria do livro a partir do objeto BeautifulSoup.
        
        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup da página do livro
            
        Returns:
            str: Categoria do livro
        """
        category_class = soup.find("ul", class_=self.class_category)

        if category_class is None:
            return ""
        
        links = category_class.find_all('a')
        if len(links) >= self.category_link_number:
            return links[self.category_link_number - 1].get_text(strip=True)
        else:
            return ""

    def extract_image_url(self, soup, book_url):
        """
        Extrai a URL da imagem do livro a partir do objeto BeautifulSoup.
        
        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup da página do livro
            book_url (str): URL da página do livro
            
        Returns:
            str: URL da imagem do livro
        """
        img_tag = soup.find("div", class_="item active")
        if img_tag:
            img_element = img_tag.find("img")
            if img_element:
                img_rel_url = img_element.get("src")
                img_full_url = urljoin(book_url, img_rel_url)
                return img_full_url
        return ""

    def extract_rating(self, soup):
        """
        Extrai a avaliação (rating) do livro em formato numérico.
        
        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup da página do livro
            
        Returns:
            int: Rating do livro (1-5), 0 se não encontrado
        """
        star_rating_element = soup.find("p", class_='star-rating')
        if star_rating_element:
            star_classes = star_rating_element.get("class")
            if len(star_classes) >= 2:
                star_text = star_classes[1]
                return self._convert_text_to_number(star_text)
        return 0

    def extract_table_data(self, soup_table):
        """
        Extrai os dados de uma tabela HTML e retorna um dicionário.
        
        Args:
            soup_table (BeautifulSoup): Objeto BeautifulSoup da tabela HTML
            
        Returns:
            dict: Dicionário com os dados da tabela (chave: th, valor: td)
        """
        table_data = {}
        rows = soup_table.find_all('tr')
        for row in rows:
            th = row.find('th')
            td = row.find('td')
            if th and td:
                table_data[th.get_text(strip=True)] = td.get_text(strip=True)
        return table_data

    def extract_product_info(self, soup):
        """
        Extrai informações da tabela de Product Information.
        
        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup da página do livro
            
        Returns:
            dict: Dicionário com informações do produto (UPC, preço, estoque, etc.)
        """
        table_prod_info = soup.find("table", class_='table')
        if table_prod_info:
            return self.extract_table_data(table_prod_info)
        return {}

    def extract_description(self, soup):
        """
        Extrai a descrição do livro.
        
        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup da página do livro
            
        Returns:
            str: Descrição do livro
        """
        description_div = soup.find("div", id="product_description")
        if description_div:
            next_p = description_div.find_next('p')
            if next_p:
                return next_p.get_text(strip=True)
        return ""

    def extract_links_from_page(self, soup, base_url, remove_empty_names=True):
        """
        Extrai todos os links de uma página e retorna um dicionário.
        
        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup da página
            base_url (str): URL base para resolver URLs relativas
            remove_empty_names (bool): Se True, remove entradas com nomes vazios
            
        Returns:
            dict: Dicionário com URLs como chaves e nomes como valores
        """
        links = soup.find_all('a')
        page_urls = {}
        
        for link in links:
            url_relativo = link.get('href')
            if url_relativo:
                url_link = urljoin(base_url, url_relativo)
                nome_link = link.get_text(strip=True)
                
                if (not remove_empty_names) or len(nome_link) > 0:
                    page_urls[url_link] = nome_link
                    
        return page_urls

    def extract_book_data_complete(self, soup, book_url, index):
        """
        Extrai todos os dados de um livro de forma completa.
        
        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup da página do livro
            book_url (str): URL da página do livro
            index (int): Índice do livro na lista
            
        Returns:
            dict: Dicionário completo com todos os dados do livro
        """
        book_data = {'index': index}

        # Dados básicos
        book_data['title'] = self.extract_title(soup)
        book_data['category'] = self.extract_category(soup)
        book_data['image_url'] = self.extract_image_url(soup, book_url)
        book_data['rating'] = self.extract_rating(soup)

        # Informações da tabela de produto
        prod_info = self.extract_product_info(soup)
        if prod_info:
            book_data['upc'] = prod_info.get('UPC', '')
            
            # Processamento de preço e taxa
            price_text = prod_info.get('Price (excl. tax)', '£0')
            book_data['price'] = self._extract_price_value(price_text)
            
            tax_text = prod_info.get('Tax', '£0')
            book_data['tax'] = self._extract_price_value(tax_text)
            
            # Processamento de estoque
            availability_text = prod_info.get('Availability', '0')
            book_data['stock'] = self._extract_stock_value(availability_text)
            
            # Número de reviews
            reviews_text = prod_info.get('Number of reviews', '0')
            book_data['reviews'] = self._extract_number_value(reviews_text)

        # Descrição
        book_data['description'] = self.extract_description(soup)

        return book_data

    def _convert_text_to_number(self, text):
        """
        Converte uma classificação em texto para um número.
        
        Args:
            text (str): Texto da classificação (One, Two, etc.)
            
        Returns:
            int: Número correspondente (1-5), 0 se não encontrado
        """
        text_to_number = {
            "One": 1,
            "Two": 2,
            "Three": 3,
            "Four": 4,
            "Five": 5
        }
        return text_to_number.get(text, 0)

    def _extract_price_value(self, price_text):
        """
        Extrai valor numérico de um texto de preço.
        
        Args:
            price_text (str): Texto do preço (ex: "£51.77")
            
        Returns:
            float: Valor numérico do preço
        """
        try:
            return float(price_text.replace('£', '').strip())
        except (ValueError, AttributeError):
            return 0.0

    def _extract_stock_value(self, availability_text):
        """
        Extrai quantidade em estoque do texto de disponibilidade.
        
        Args:
            availability_text (str): Texto de disponibilidade
            
        Returns:
            int: Quantidade em estoque
        """
        try:
            # Remove texto padrão e extrai número
            stock_text = availability_text.replace('In stock (', '').replace(' available)', '').strip()
            return int(stock_text)
        except (ValueError, AttributeError):
            return 0

    def _extract_number_value(self, text):
        """
        Extrai valor numérico de um texto.
        
        Args:
            text (str): Texto contendo número
            
        Returns:
            int: Valor numérico extraído
        """
        try:
            return int(text.strip())
        except (ValueError, AttributeError):
            return 0
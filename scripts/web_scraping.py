import requests
from bs4 import BeautifulSoup
import pandas as pd
import os


# Parametros configuráveis da página
div_categorias = 'side_categories'
nome_link_books = 'Books'

# A categoria está dentro de uma 'ul' com a classe definida em class_category e é o link de número category_link_number dentro dessa 'ul'
class_category = 'breadcrumb'
category_link_number = 3

scraping_database_file = './data/scraping_books_database.csv'


# Funcoes de extracao de dados de livros

def web_scraping_data_init():
    
    web_scraping_data = {}

    try:
        web_scraping_data["books_dataframe"] = pd.read_csv(scraping_database_file)
        if len(web_scraping_data["books_dataframe"]) > 0:
            web_scraping_data["scraping_status"] = "Done"
            web_scraping_data["qtd_books"] = len(web_scraping_data["books_dataframe"])
    except FileNotFoundError:
        web_scraping_data["scraping_status"] = "Idle"
        web_scraping_data["books_dataframe"] = pd.DataFrame()
        web_scraping_data["qtd_books"] = 0

    return web_scraping_data

def web_scraping_get_status(web_scraping_data):
    return web_scraping_data["scraping_status"]

def web_scraping_set_status(web_scraping_data, status):
    web_scraping_data["scraping_status"] = status

    if status == "Idle":
        web_scraping_data["qtd_books"] = 0
        web_scraping_data["books_dataframe"] = []

def  web_scraping_get_database(web_scraping_data):
    return web_scraping_data["books_dataframe"]

# Realiza a requisicao HTTP e retorna o objeto BeautifulSoup
def url_get_soup(url):
    response = requests.get(url)
    response.encoding = response.apparent_encoding
    
    if response.status_code == 200:
        html_content = response.text  # Pegamos o conteúdo HTML.
    else:
        print(f"Erro ao acessar a página. Código de status: {response.status_code}")
        return None

    return BeautifulSoup(html_content, 'html.parser')

# Gera o link a partir do url atual e a url relativa do link
# O link relativo pode ter varios niveis de "../", portanto a funcao trata cada um como um retorno de pasta
def gera_url_de_relativo (url_atual, url_relativo):
    # Conta a quantidade de niveis "../" no link relativo e remove do link
    qtd_level = url_relativo.count("../")
    url_relativo_final = url_relativo.replace("../", "")

    # Remove o final do url atual, deixando apenas o path e separa em niveis
    url_atual_path = url_atual[:url_atual.rfind("/")+1]
    url_parts = url_atual_path.strip("/").split("/")

    # Remove os niveis do path de acordo com a quantidade de niveis "../" do link relativo
    if qtd_level > 0 and len(url_parts) >= qtd_level:
        url_parts = url_parts[:-qtd_level]

    # Adiciona o link relativo ao path e retorna o link completo
    return "/".join(url_parts + [url_relativo_final])

# Extrai todos os links da página, retornando um dicionario com o link completo e o nome do link
# Se remove_nome_vazio for True, remove os links que não possuem nome
def extrai_urls (soup, url, remove_nome_vazio):
    links = soup.find_all('a')
    base_urls = {}
    for link in links:
        url_relativo = link.get('href')
        url_link = gera_url_de_relativo(url, url_relativo)
        nome_link = link.get_text(strip=True)
        if (not remove_nome_vazio) or len(nome_link) > 0:
            base_urls[url_link] = nome_link
    return base_urls

# Extrai o valor de um dicionario e remove a chave/valor do dicionario
def dic_extrai_valor (dicionario, valor):
    for key in dicionario:
        if dicionario[key] == valor:
            del dicionario[key]
            return key
    return None


# Extrai os links de livros de uma página e retorna o dicionario com os links e o link da próxima página (se existir)
def extrai_links_book (url, book_dic):
    response = requests.get(url)

    if response.status_code == 200:
        html_content = response.text  # Pegamos o conteúdo HTML.
    else:
        print(f"Erro ao acessar a página. Código de status: {response.status_code}")

    soup_books = BeautifulSoup(html_content, 'html.parser')
    soup_books_section = soup_books.find('section')

    books_url_pag_atual = extrai_urls (soup_books_section, url, True)
    link_next = dic_extrai_valor(books_url_pag_atual, 'next')
    link_previous = dic_extrai_valor(books_url_pag_atual, 'previous')

    book_dic = book_dic | books_url_pag_atual
    return book_dic, link_next



## Parte 3: Extração dos dados de cada livro
# - Os campos serão: title, price, stock, category, rating, description

# Extrai o tiulo do livro (em 'li' na classe 'active')
def soup_get_title (soup):
    return soup.find("li", class_= "active").get_text(strip=True)

# Extrai a categoria dentro da 'ul' na classe definida em class_category 
def soup_get_category (soup):
    category_class = soup.find("ul", class_= class_category)

    links = category_class.find_all('a')
    if len(links) >= category_link_number:
        return links[category_link_number-1].get_text(strip=True)
    else:
        return ""


def soup_get_image_url (soup, url_atual):
    img_tag = soup.find("img")
    if img_tag and img_tag.has_attr('src'):
        image_path = img_tag['src']
        return gera_url_de_relativo(url_atual, image_path)
    else:
        return None
    

# Extrai os dados da tabela de informações do livro (dentro de 'table' na classe 'table table-striped')
def soup_table_get_data (soup_table):
    soup_data = {}
    rows = soup_table.find_all('tr')
    for row in rows:
        soup_data[row.find('th').get_text(strip=True)] = row.find('td').get_text(strip=True)
    return soup_data

# Converte o texto do rating em número ( One, Two, Three, Four, Five)
def convert_text_to_number(text):
    text_to_number = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }
    return text_to_number.get(text, 0)


# Extrai os dados do livro a partir da url da pagina do livro
def soup_extract_book_data (book_url, indice):
    book_data = {}

    soup_book = url_get_soup(book_url)

    book_data['index'] = indice

    # Extracao das variaveis do livro: Titulo, Categoria, URL da imagem, Rating (em numero), UPC, Price, Taxa, Stock, Reviews, Descrição
    book_data['title'] = soup_get_title(soup_book)
    book_data['category'] = soup_get_category(soup_book)
    book_data['image_url'] = soup_get_image_url(soup_book, book_url)

    star_rating = soup_book.find("p",class_ = 'star-rating').get("class")[1]
    book_data['rating'] = convert_text_to_number(star_rating)

    # Leitura da tabela de Product Information
    table_prod_info = soup_book.find("table", class_ = 'table')
    prod_info_dic = soup_table_get_data(table_prod_info)
    book_data['upc'] = prod_info_dic['UPC']
    book_data['price'] = float(prod_info_dic['Price (excl. tax)'].replace('£',''))
    book_data['tax'] = float(prod_info_dic['Tax'].replace('£',''))
    book_data['stock'] = int(prod_info_dic['Availability'].replace('In stock (','').replace(' available)','').strip())
    book_data['reviews'] = int(prod_info_dic['Number of reviews'].strip())

    #Extrai descrição
    soup_description_div = soup_book.find("div", id="product_description")
    if soup_description_div: 
        book_data['description'] = soup_description_div.find_next('p').get_text(strip=True)
    else:
        book_data['description'] = ''
        
    return book_data


def web_scraping_get_books_url (url):

    print("Iniciando o scraping...")
    ## Parte 1: Leitura da página principal
    # - Realiza a leitura do link principal
    # - Localiza o link da página que mostra todos os livros

    # Realiza a leitura da página principal
    soup_principal = url_get_soup(url)

    dic_urls_principal = extrai_urls(soup_principal, url = url, remove_nome_vazio = True)
    # localiza a url para a página dos livros
    url_pagina_books = dic_extrai_valor(dic_urls_principal, nome_link_books)

    ## Parte 2: Leitura da página de livros
    # - Realiza a leitura da página de livros
    # - Localiza a área com os livros (dentro de section)
    # - Extrai o link de cada livro
    # - Recursivo até não achar mais link de next

    # Inicia o dicionario de url de livros
    dic_url_books = {}
    url_next = url_pagina_books

    # Loop para extrair os links de todas as páginas até não existir mais página next
    while (url_next != None):
        print("Extraindo links de página: ", url_next)
        dic_url_books, url_next = extrai_links_book(url_next, dic_url_books)
    return dic_url_books



def web_scraping (url):

    print("Iniciando o scraping...")
    ## Parte 1: Leitura da página principal
    # - Realiza a leitura do link principal
    # - Localiza o link da página que mostra todos os livros

    # Realiza a leitura da página principal
    soup_principal = url_get_soup(url)

    dic_urls_principal = extrai_urls(soup_principal, url = url, remove_nome_vazio = True)
    # localiza a url para a página dos livros
    url_pagina_books = dic_extrai_valor(dic_urls_principal, nome_link_books)

    ## Parte 2: Leitura da página de livros
    # - Realiza a leitura da página de livros
    # - Localiza a área com os livros (dentro de section)
    # - Extrai o link de cada livro
    # - Recursivo até não achar mais link de next

    # Inicia o dicionario de url de livros
    dic_url_books = {}
    url_next = url_pagina_books

    # Loop para extrair os links de todas as páginas até não existir mais página next
    while (url_next != None):
        dic_url_books, url_next = extrai_links_book(url_next, dic_url_books)


    # looping para extrair os dados de cada livro e montar o dataframe final
    indice = 0
    books_base = []
    for book_url in dic_url_books:
        if indice % 50 == 0:
            print(indice)
        book_data = soup_extract_book_data(book_url, indice)
        book_df = pd.DataFrame([book_data])
        if len(books_base) == 0:
            books_base = book_df
        else:
            books_base = pd.concat([books_base, book_df], ignore_index=True)
        indice += 1

    return books_base
    # Salvando a base de dados em CSV
    #books_base.to_csv('scraping_books_database.csv', index = False)


def web_scraping_status_message(web_scraping_data):
    """
    Returns a status message for the web scraping process.

    Parameters:
        web_scraping_data (dict): Dictionary containing the current scraping status and book data.

    Returns:
        str: A message indicating the current state of the scraping process.
    """

    if web_scraping_get_status(web_scraping_data) == "Running":
        if web_scraping_data["qtd_books"] == 0:
            return "Scraping em andamento: Extraindo url dos livros. (Aguarde...)"
        else:
            perc_scraped = (len(web_scraping_data["books_dataframe"]) / web_scraping_data["qtd_books"]) * 100
            return f"Scraping em andamento: {perc_scraped:.2f}%."
    elif web_scraping_get_status(web_scraping_data) == "Done":
        return "Scraping concluído."
    else:
        return "Scraping não iniciado."
    
def web_scraping_task (url, web_scraping_data):        
    
    web_scraping_data["scraping_status"] = "Running"
    web_scraping_data["books_dataframe"] = []
    
    print("Iniciando o scraping em background...")
    books_url = web_scraping_get_books_url(url)
    
    web_scraping_data["qtd_books"] = len(books_url)

    print("Total de livros para scraping: ", web_scraping_data["qtd_books"])

    indice = 0
    
    for book_url in books_url:
        if web_scraping_data["scraping_status"] == "Stopping":
            web_scraping_data["scraping_status"] = "Idle"
            return
        book_data = soup_extract_book_data(book_url, indice)
        book_df = pd.DataFrame([book_data])
        if len(web_scraping_data["books_dataframe"]) == 0:
            web_scraping_data["books_dataframe"] = book_df
        else:
            web_scraping_data["books_dataframe"] = pd.concat([web_scraping_data["books_dataframe"], book_df], ignore_index=True)
        indice += 1

    web_scraping_data["scraping_status"] = "Done"

    web_scraping_data["books_dataframe"].to_csv(scraping_database_file, index=False)
    return web_scraping_data["books_dataframe"]

def web_scraping_delete_database():
    if os.path.exists(scraping_database_file):
        os.remove(scraping_database_file)

def web_scraping_size(web_scraping_data):
    return len(web_scraping_data["books_dataframe"])

from fastapi import FastAPI
from fastapi import Depends, HTTPException, status
from fastapi import BackgroundTasks
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import pandas as pd
import scripts.web_scraping as scrap
from time import sleep

url = 'https://books.toscrape.com/'


app = FastAPI(
    title="Books scraping API",
    version="1.0",
    description="API web de scraping de página web de livros utilizando FastAPI e BeautifulSoup",
)

print("Iniciando web scraping...")
web_scraping = scrap.web_scraping_data_init()
print("Web scraping iniciado.")

@app.get("/api/v1/books")
async def get_books_titles():
    """
    Retorna a lista de títulos dos livros scraped.
    """

    if scrap.web_scraping_get_status(web_scraping) != "Done":
        return {"message": scrap.web_scraping_status_message(web_scraping)}

    return scrap.web_scraping_get_book_titles(web_scraping)
    
@app.get("/api/v1/books/scraping_start")
def start_scraping(background_tasks: BackgroundTasks):
    """
    Inicia o processo de scraping em background.
    """

    if scrap.web_scraping_get_status(web_scraping) == "Idle":
        print("Iniciando task...")
        background_tasks.add_task(scrap.web_scraping_task, url, web_scraping)
        return {"message": "scraping iniciado em background."}
    else:
        return {"message": scrap.web_scraping_status_message(web_scraping)}


@app.get("/api/v1/books/scraping_reset")
def delete_scraping():
    """
    Deleta a base de dados de scraping.
    """    
    
    # Caso o scraping esteja em andamento, aguardar a task parar
    if scrap.web_scraping_get_status(web_scraping) == "Running":
        scrap.web_scraping_set_status(web_scraping, "Stopping")
        while scrap.web_scraping_get_status(web_scraping) == "Stopping":
            # Esperar o término do scraping
            sleep(1)

    scrap.web_scraping_delete_database()

    scrap.web_scraping_set_status(web_scraping, "Idle")

    return {"message": "Base de dados de scraping deletada com sucesso."}


@app.get("/api/v1/books/search")
async def get_books_search(title: str = None, category: str = None):
    """
    Retorna a lista de títulos dos livros filtrados por título e/ou categoria.
    """

    books_search = scrap.web_scraping_get_database(web_scraping)
    
    if scrap.web_scraping_get_status(web_scraping) != "Done":
        return {"message": scrap.web_scraping_status_message(web_scraping)}

    if category:
        print(category)
        print(books_search)
        books_search = books_search[books_search['category'].str.contains(category, case=False)]
    
    if title:
        print(title)
        books_search = books_search[books_search['title'].str.contains(title, case=False)]
    
    if(len(books_search) > 0):
        return {"titles": books_search['title'].tolist()}
    else:
        return {"titles": []}


@app.get("/api/v1/books/categories")
async def get_book_categories():
    """
    Retorna a lista de categorias dos livros scraped.
    """

    if scrap.web_scraping_get_status(web_scraping) != "Done":
        return {"message": scrap.web_scraping_status_message(web_scraping)}

    books_dataframe = scrap.web_scraping_get_database(web_scraping)
    return {"categories": sorted(books_dataframe['category'].unique().tolist())}


@app.get("/api/v1/health")
async def health_check():
    """
    Retorna o status da API e do scraping.
    """    
    
    api_status = "online"
    
    if scrap.web_scraping_get_status(web_scraping) == "Done":
        return {
            "api": api_status,
            "scraping status": scrap.web_scraping_status_message(web_scraping),
            "books_scraped": scrap.web_scraping_size(web_scraping)
        }
    else:
        return {
            "api": api_status,
            "scraping status": scrap.web_scraping_status_message(web_scraping)
        }


@app.get("/api/v1/books/{id}")
async def get_books(id: int):
    """
    Retorna os detalhes de um livro específico pelo seu ID.
    """


    if scrap.web_scraping_get_status(web_scraping) != "Done":
        return {"message": scrap.web_scraping_status_message(web_scraping)}

    if id >= 0 and id < scrap.web_scraping_size(web_scraping):
        books_dataframe = scrap.web_scraping_get_database(web_scraping)
        return books_dataframe.iloc[id].to_dict()
    else:
        raise HTTPException(status_code=404, detail="Book item not found")
     

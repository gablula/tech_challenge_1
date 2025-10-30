from fastapi import FastAPI
from fastapi import Depends, HTTPException, status
from fastapi import BackgroundTasks
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import pandas as pd
import scripts.web_scrapping as scrap
from time import sleep

url = 'https://books.toscrape.com/'


app = FastAPI(
    title="Books Scrapping API",
    version="1.0",
    description="API web de Scrapping de página web de livros utilizando FastAPI e BeautifulSoup",
)

print("Iniciando web scrapping...")
web_scrapping = scrap.web_scrapping_data_init()
print("Web scrapping iniciado.")

@app.get("/api/v1/books")
async def get_books_titles():
    """
    Retorna a lista de títulos dos livros scrapped.
    """

    if scrap.web_scrapping_get_status(web_scrapping) != "Done":
        return {"message": scrap.web_scrapping_status_message(web_scrapping)}

    return scrap.web_scrapping_get_book_titles(web_scrapping)
    
@app.get("/api/v1/books/scrapping_start")
def start_scraping(background_tasks: BackgroundTasks):
    """
    Inicia o processo de scrapping em background.
    """

    if scrap.web_scrapping_get_status(web_scrapping) == "Idle":
        print("Iniciando task...")
        background_tasks.add_task(scrap.web_scrapping_task, url, web_scrapping)
        return {"message": "Scrapping iniciado em background."}
    else:
        return {"message": scrap.web_scrapping_status_message(web_scrapping)}


@app.get("/api/v1/books/scrapping_reset")
def delete_scrapping():
    """
    Deleta a base de dados de scrapping.
    """    
    
    # Caso o scrapping esteja em andamento, aguardar a task parar
    if scrap.web_scrapping_get_status(web_scrapping) == "Running":
        scrap.web_scrapping_set_status(web_scrapping, "Stopping")
        while scrap.web_scrapping_get_status(web_scrapping) == "Stopping":
            # Esperar o término do scrapping
            sleep(1)

    scrap.web_scrapping_delete_database()

    scrap.web_scrapping_set_status(web_scrapping, "Idle")

    return {"message": "Base de dados de scrapping deletada com sucesso."}


@app.get("/api/v1/books/search")
async def get_books_search(title: str = None, category: str = None):
    """
    Retorna a lista de títulos dos livros filtrados por título e/ou categoria.
    """

    books_search = scrap.web_scrapping_get_database(web_scrapping)
    
    if scrap.web_scrapping_get_status(web_scrapping) != "Done":
        return {"message": scrap.web_scrapping_status_message(web_scrapping)}

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
    Retorna a lista de categorias dos livros scrapped.
    """

    if scrap.web_scrapping_get_status(web_scrapping) != "Done":
        return {"message": scrap.web_scrapping_status_message(web_scrapping)}

    books_dataframe = scrap.web_scrapping_get_database(web_scrapping)
    return {"categories": sorted(books_dataframe['category'].unique().tolist())}


@app.get("/api/v1/health")
async def health_check():
    """
    Retorna o status da API e do scrapping.
    """    
    
    api_status = "online"
    
    if scrap.web_scrapping_get_status(web_scrapping) == "Done":
        return {
            "api": api_status,
            "scraping status": scrap.web_scrapping_status_message(web_scrapping),
            "books_scrapped": scrap.web_scrapping_size(web_scrapping)
        }
    else:
        return {
            "api": api_status,
            "scraping status": scrap.web_scrapping_status_message(web_scrapping)
        }


@app.get("/api/v1/books/{id}")
async def get_books(id: int):
    """
    Retorna os detalhes de um livro específico pelo seu ID.
    """


    if scrap.web_scrapping_get_status(web_scrapping) != "Done":
        return {"message": scrap.web_scrapping_status_message(web_scrapping)}

    if id >= 0 and id < scrap.web_scrapping_size(web_scrapping):
        books_dataframe = scrap.web_scrapping_get_database(web_scrapping)
        return books_dataframe.iloc[id].to_dict()
    else:
        raise HTTPException(status_code=404, detail="Book item not found")
     

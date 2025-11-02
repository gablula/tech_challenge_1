from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import time
from datetime import datetime

from services.web_scraper import WebScraper

# Modelos Pydantic para documentação
class ScrapingStatusResponse(BaseModel):
    status: str
    books_count: int
    message: str

class MessageResponse(BaseModel):
    message: str

class HealthResponse(BaseModel):
    api_status: str
    uptime_seconds: float
    scraping_status: str
    books_scraped: Optional[int] = None
    csv_file_size_mb: Optional[float] = None
    csv_creation_date: Optional[str] = None

class CategoriesResponse(BaseModel):
    categories: List[str]

class BookResponse(BaseModel):
    title: Optional[str] = None
    price: Optional[str] = None
    category: Optional[str] = None
    availability: Optional[str] = None
    rating: Optional[str] = None
    description: Optional[str] = None

router = APIRouter()
scraper = WebScraper()

# Variável para controlar o tempo de início da aplicação
app_start_time = time.time()


@router.get(
    "/",
    summary="Página Inicial",
    description="Redireciona para a documentação da API",
    tags=["Sistema"]
)
async def root():
    """Redireciona para a documentação Swagger da API"""
    return RedirectResponse(url="/docs")


@router.get(
    "/api/v1/scraper/status",
    response_model=ScrapingStatusResponse,
    summary="Obter Status do Scraping",
    description="Retorna o status atual do processo de scraping",
    tags=["Scraping"]
)
def get_scraping_status():
    """
    **Obtém o status atual do scraping**
    
    Retorna informações sobre:
    - Status atual do processo (Idle, Running, Done, etc.)
    - Mensagem descritiva do status
    """
    data = {
        "status": scraper.state.status,
        "message": scraper.get_status_message()
    }
    return JSONResponse(content=data)

@router.get(
    "/api/v1/scraper/start",
    response_model=MessageResponse,
    summary="Iniciar Scraping",
    description="Inicia o processo de scraping em background para coletar dados de livros do site.",
    tags=["Scraping"]
)
def start_scraping(background_tasks: BackgroundTasks):
    """
    **Inicia o processo de scraping de livros**
    
    - Se o scraper estiver inativo (Idle), inicia a coleta em background
    - Se já estiver rodando ou finalizado, retorna o status atual
    - O processo roda de forma assíncrona sem bloquear a API
    """
    if scraper.state.status == "Idle":
        background_tasks.add_task(scraper.scraper_task)
        return {"message": "Scraping iniciado em background."}
    return {"message": scraper.get_status_message()}

@router.get(
    "/api/v1/scraper/reset",
    response_model=MessageResponse,
    summary="Resetar Scraping",
    description="Para o processo de scraping (se estiver rodando) e limpa toda a base de dados coletada.",
    tags=["Scraping"]
)
def reset_scraping():
    """
    **Reseta o processo de scraping**
    
    - Para o scraping se estiver em execução
    - Remove todos os dados coletados
    - Reseta o contador de livros
    - Retorna o status para 'Idle'
    
    """
    if scraper.state.status in ["Running", "Extracting_urls", "Scraping_books"]:
        scraper.state.status = "Stopping"
        while scraper.state.status == "Stopping":
            pass  # Esperar a task de scraping parar
    scraper.delete_database()
    scraper.state.status = "Idle"
    scraper.state.qtd_books_urls = 0
    return {"message": "Base de dados de scraping apagada com sucesso."}


@router.get(
    "/api/v1/books",
    response_model=List[str],
    summary="Listar Títulos dos Livros",
    description="Retorna uma lista com todos os títulos dos livros coletados pelo scraping.",
    tags=["Livros"]
)
async def get_books_titles():
    """
    **Obtém lista de títulos de todos os livros**
    
    - Retorna apenas os títulos dos livros coletados
    - Requer que o scraping tenha sido concluído (status 'Done')
    - Útil para obter uma visão geral rápida do catálogo
    """
    if scraper.state.status != "Done":
        data = {"message": scraper.get_status_message()}
        return JSONResponse(content=data)
    
    titles = scraper.get_book_titles()
    return JSONResponse(content=titles)


@router.get(
    "/api/v1/books/search",
    response_model=List[Dict[str, Any]],
    summary="Buscar Livros",
    description="Busca livros por título e/ou categoria com filtros opcionais.",
    tags=["Livros"]
)
async def get_books_search(
    title: Optional[str] = Query(None, description="Filtrar por título (busca parcial, case-insensitive)"),
    category: Optional[str] = Query(None, description="Filtrar por categoria exata")
):
    """
    **Busca livros com filtros opcionais**
    
    Parâmetros de busca:
    - **title**: Busca parcial no título (não diferencia maiúsculas/minúsculas)
    - **category**: Busca exata por categoria
    
    Exemplos de uso:
    - `/api/v1/books/search?title=python` - livros com "python" no título
    - `/api/v1/books/search?category=Fiction` - livros da categoria Fiction
    - `/api/v1/books/search?title=data&category=Science` - combinação de filtros
    """
    if scraper.state.status != "Done":
        data = {"message": scraper.get_status_message()}
        return JSONResponse(content=data)
    
    results = scraper.search_books(title=title, category=category)
    return JSONResponse(content=results)




@router.get(
    "/api/v1/books/categories",
    response_model=CategoriesResponse,
    summary="Listar Categorias",
    description="Retorna todas as categorias únicas encontradas nos livros coletados.",
    tags=["Livros"]
)
async def get_categories():
    """
    **Obtém lista de todas as categorias disponíveis**
    
    - Retorna categorias únicas dos livros coletados
    - Lista ordenada alfabeticamente
    - Útil para filtros e navegação por categoria
    """
    if scraper.state.status != "Done":
        data = {"message": scraper.get_status_message()}
        return JSONResponse(content=data)

    if 'category' not in scraper.state.books_dataframe.columns:
        data = {"message": "A coluna 'category' não foi encontrada na base de dados."}
        return JSONResponse(content=data)
    
    categories = {"categories": sorted(scraper.state.books_dataframe['category'].unique().tolist())}
    return JSONResponse(content=categories)



@router.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="Verificar Status da API",
    description="Endpoint de health check que retorna informações essenciais sobre a API e o scraping.",
    tags=["Sistema"]
)
async def health_check():
    """
    **Health check da API**
    
    Retorna informações essenciais:
    - ⏱️ Tempo de execução da API
    - 🟢 Status da API
    - 🔄 Status do scraping
    - 📚 Quantidade de livros coletados
    - 📁 Tamanho do arquivo CSV
    - 📅 Data de criação do arquivo CSV
    
    Útil para monitoramento básico e verificação de saúde do serviço.
    """
    # Tempo de execução da API
    uptime_seconds = round(time.time() - app_start_time, 2)
    
    # Status da API
    api_status = "online"
    
    # Status do scraping e quantidade de livros
    scraping_status = scraper.get_status_message()
    books_count = scraper.state.qtd_books_urls if hasattr(scraper.state, 'qtd_books_urls') else 0
    
    # Informações do arquivo CSV
    csv_size_mb = None
    csv_creation_date = None
    
    database_path = scraper.SCRAPING_DATABASE_FILE
    try:
        if os.path.exists(database_path):
            # Tamanho do arquivo em MB
            size_bytes = os.path.getsize(database_path)
            csv_size_mb = round(size_bytes / (1024 * 1024), 3)
            
            # Data de criação do arquivo
            creation_timestamp = os.path.getctime(database_path)
            csv_creation_date = datetime.fromtimestamp(creation_timestamp).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        # Se houver erro ao acessar o arquivo, mantenha os valores None
        pass
    
    # Retornar JSON formatado (pretty-printed)
    data = {
        "api_status": api_status,
        "uptime_seconds": uptime_seconds,
        "scraping_status": scraping_status,
        "books_scraped": books_count if books_count > 0 else None,
        "csv_file_size_mb": csv_size_mb,
        "csv_creation_date": csv_creation_date
    }
    
    # Retorna JSON com indentação para melhor legibilidade
    return JSONResponse(content=data, headers={"Content-Type": "application/json; charset=utf-8"})
    

@router.get(
    "/api/v1/books/{id}",
    response_model=BookResponse,
    summary="Obter Livro por ID",
    description="Retorna os detalhes completos de um livro específico baseado no seu ID (índice de 0 até total-1).",
    tags=["Livros"],
    responses={
        200: {
            "description": "Livro encontrado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "title": "A Light in the Attic",
                        "price": "£51.77",
                        "category": "Poetry",
                        "availability": "In stock",
                        "rating": "Three",
                        "description": "It's hard to imagine a world without A Light in the Attic..."
                    }
                }
            }
        },
        404: {
            "description": "Livro não encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Livro não encontrado. Índice deve estar entre 0 e o total de livros coletados."}
                }
            }
        }
    }
)
async def get_book_by_id(id: int):
    """
    **Obtém detalhes completos de um livro por ID**
    
    - **id**: Índice do livro na base de dados (começa em 0)
    - **Range válido**: 0 até (total de livros - 1)
    - Retorna todas as informações disponíveis do livro
    - Inclui título, preço, categoria, disponibilidade, avaliação e descrição
    
    **Exemplos**:
    - `/api/v1/books/0` - retorna o primeiro livro da coleção
    - `/api/v1/books/999` - retorna o livro de índice 999 (se existir)
    
    **Nota**: Para verificar quantos livros foram coletados, use `/api/v1/scraper/status`
    """
    if scraper.state.status != "Done":
        data = {"message": scraper.get_status_message()}
        return JSONResponse(content=data)

    # Verificar se o DataFrame existe e tem dados
    if not hasattr(scraper.state, 'books_dataframe') or scraper.state.books_dataframe.empty:
        data = {"message": "Nenhum livro foi coletado ainda. Execute o scraping primeiro."}
        return JSONResponse(content=data)
    
    total_books = len(scraper.state.books_dataframe)
    
    if id >= 0 and id < total_books:
        book_data = scraper.state.books_dataframe.iloc[id].to_dict()
        return JSONResponse(content=book_data)
    else:
        raise HTTPException(
            status_code=404, 
            detail=f"Livro não encontrado. Índice deve estar entre 0 e {total_books - 1}. Total de livros disponíveis: {total_books}"
        )
     
from fastapi import FastAPI
from api.routes import router
import uvicorn
import os

app = FastAPI(
    title="Books Scraper API",
    description="""
    ## API de Scraping de Livros
    
    Esta API permite fazer scraping de dados de livros do site Books to Scrape e consultar os dados coletados.
    
    ### Funcionalidades principais:
    - **Controle de Scraping**: Iniciar, parar e resetar o processo de coleta
    - **Consulta de Livros**: Buscar livros por título, categoria ou ID
    - **Monitoramento**: Verificar status do processo e saúde da API
    
    ### Como usar:
    1. **Inicie o scraping** em `/api/v1/scraper/start`
    2. **Monitore o progresso** em `/api/v1/books/scraping_status`
    3. **Consulte os dados** quando o status for 'Done'
    
    ### Tags:
    - **Scraping**: Operações de controle do processo de coleta
    - **Livros**: Consulta e busca de dados dos livros
    - **Sistema**: Monitoramento e health checks
    """,
    version="1.0.0",
    contact={
        "name": "Gabriel Wense",
        "email": "gabriel.wense@gmail.com",
    },
)

# Incluir as rotas
app.include_router(router)

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host=host, port=port)

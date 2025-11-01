from fastapi import FastAPI
from api.routes import router
import uvicorn

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
        "name": "Gabrieel Wense",
        "email": "gabriel.wense@gmail.com",
    },
)

# Incluir as rotas
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
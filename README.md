# Books Scraper API

## Descrição do Projeto

A **Books Scraper API** é uma aplicação desenvolvida em Python com FastAPI que realiza web scraping do site [Books to Scrape](https://books.toscrape.com/) e disponibiliza os dados coletados através de uma API REST documentada com Swagger.

### Objetivo
Coletar informações de livros (título, preço, categoria, disponibilidade, avaliação e descrição) e disponibilizar esses dados através de endpoints REST para consulta, busca e análise.

### Funcionalidades Principais
- **Scraping Automatizado**: Coleta dados de todas as páginas do site
- **Busca Avançada**: Filtros por título e categoria
- **Monitoramento**: Status em tempo real do processo de scraping
- **Documentação Interativa**: Swagger UI integrado
- **Organização por Tags**: Endpoints organizados por funcionalidade
- **Arquitetura Modular**: Código organizado em módulos especializados
---

## Arquitetura do Projeto

```
tech_challenge_1/                # Repositório Git
├── main.py                      # Aplicação principal FastAPI
├── requirements.txt             # Dependências do projeto
├── api/
│   ├── __init__.py
│   └── routes.py                # Definição das rotas da API
├── services/
│   ├── __init__.py
│   ├── web_scraper.py           # Orquestrador principal de scraping
│   ├── html_parser.py           # Parser HTML com BeautifulSoup
│   └── scraper_utils.py         # Utilitários e helpers de scraping
├── data/
│   └── scraping_books_database.csv  # Base de dados CSV (gerado automaticamente)
└── README.md                    # Documentação do projeto
```

### Componentes da Arquitetura

1. **FastAPI Application** (`main.py`)
   - Configuração da aplicação principal

2. **API Routes** (`api/routes.py`)
   - Endpoints REST organizados por tags
   - Modelos Pydantic para validação
   - Documentação detalhada com exemplos

3. **Web Scraper Service** (`services/web_scraper.py`)
   - Classe `WebScraper` para orquestração do scraping utilizando BeautifulSoup
   - Gerenciamento de estado com `ScrapingState`


4. **HTML Parser** (`services/html_parser.py`)
   - Classe `HTMLParser` para parsing HTML
   - Extração especializada de dados dos livros
   - Processamento de elementos específicos do site

5. **Scraper Utils** (`services/scraper_utils.py`)
   - Classe `ScraperUtils` com funções utilitárias
   - Operações de rede e manipulação de dados
   - Funções auxiliares para validação e formatação

6. **Data Storage** (`data/`)
   - Armazenamento em CSV
   - Estrutura de dados com pandas DataFrame
---

## Instalação e Configuração

### Pré-requisitos
- Python 3.8 ou superior
- Git
- pip (gerenciador de pacotes Python)
- Conexão com a internet

### 1. Clone o repositório
```bash
git clone https://github.com/gablula/tech_challenge_1.git
```

### 2. Crie um ambiente virtual
```bash
# Windows PowerShell
python -m venv venv

# Linux/macOS
python3 -m venv venv
```

### 3. Ative o ambiente virtual
```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat

# Linux/macOS
source venv/bin/activate
```

### 4. Instale as dependências
```bash
pip install -r requirements.txt
```

**Dependências incluídas:**
- fastapi==0.115.0
- uvicorn[standard]==0.31.1
- pandas==2.2.3
- requests==2.32.3
- beautifulsoup4==4.12.3

---

## Instruções para Execução

### Executando a API

#### Método 1: Execução Direta
```bash
# Com ambiente virtual ativado, execute a partir da raiz do projeto
python main.py
```

**Nota:** Você pode configurar `HOST` e `PORT` via variáveis de ambiente (ex: `export HOST=127.0.0.1 PORT=8080`).

#### Método 2: Usando Uvicorn
```bash
# Com ambiente virtual ativado
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Acessando a Aplicação

Após iniciar o servidor, a API estará disponível em:
- **API Base**: http://localhost:8001
- **Documentação Swagger**: http://localhost:8001/docs
- **Documentação ReDoc**: http://localhost:8001/redoc
- **Schema OpenAPI**: http://localhost:8001/openapi.json

### Workflow de Uso

1. **Inicie a API** conforme instruções acima
2. **Acesse a documentação** em http://localhost:8001/docs
3. **Inicie o scraping** chamando `/api/v1/scraper/start`
4. **Monitore o progresso** em `/api/v1/scraper/status`
5. **Consulte os dados** quando o status for 'Done'

---

## Documentação das Rotas da API

### Tags e Organização

As rotas estão organizadas em três categorias principais:

#### **Scraping** - Controle do Processo
- Gerenciamento do processo de coleta de dados
- Monitoramento de status e progresso

#### **Livros** - Consulta de Dados
- Busca e listagem de livros coletados
- Filtros por título e categoria

#### **Sistema** - Monitoramento
- Health checks e status da API

### Lista Completa de Endpoints

| Método | Endpoint | Tag | Descrição |
|--------|----------|-----|-----------|
| `GET` | `/api/v1/scraper/status` | Scraping | Status do processo de scraping |
| `GET` | `/api/v1/scraper/start` | Scraping | Iniciar scraping em background |
| `GET` | `/api/v1/scraper/reset` | Scraping | Resetar processo e limpar dados |
| `GET` | `/api/v1/books` | Livros | Listar títulos de todos os livros |
| `GET` | `/api/v1/books/search` | Livros | Buscar livros por filtros |
| `GET` | `/api/v1/books/categories` | Livros | Listar todas as categorias |
| `GET` | `/api/v1/books/{id}` | Livros | Obter livro específico por ID |
| `GET` | `/api/v1/health` | Sistema | Health check da API |

---

## Exemplos de Chamadas e Responses

### **Scraping Endpoints**

#### 1. Verificar Status do Scraping
```http
GET /api/v1/scraper/status
```

**Response:**
```json
{
  "status": "Done",
  "books_count": 1000,
  "message": "Scraping concluído com sucesso. 1000 livros coletados."
}
```

#### 2. Iniciar Scraping
```http
GET /api/v1/scraper/start
```

**Response (Sucesso):**
```json
{
  "message": "Scraping iniciado em background."
}
```

**Response (Já em execução):**
```json
{
  "message": "Scraping já está em execução. 450 livros coletados até agora."
}
```

#### 3. Resetar Scraping
```http
GET /api/v1/scraper/reset
```

**Response:**
```json
{
  "message": "Base de dados de scraping apagada com sucesso."
}
```

### **Livros Endpoints**

#### 4. Listar Títulos dos Livros
```http
GET /api/v1/books
```

**Response:**
```json
[
  "A Light in the Attic",
  "Tipping the Velvet",
  "Soumission",
  "Sharp Objects",
  "Sapiens: A Brief History of Humankind"
]
```

#### 5. Buscar Livros com Filtros
```http
GET /api/v1/books/search?title=python&category=Programming
```

**Response:**
```json
[
  {
    "title": "Learning Python",
    "price": "£30.23",
    "category": "Programming",
    "availability": "In stock (19 available)",
    "rating": "Four",
    "description": "Get a comprehensive, in-depth introduction to the core Python language..."
  }
]
```

#### 6. Listar Categorias
```http
GET /api/v1/books/categories
```

**Response:**
```json
{
  "categories": [
    "Art",
    "Biography", 
    "Business",
    "Fiction",
    "History",
    "Poetry",
    "Programming",
    "Science"
  ]
}
```

#### 7. Obter Livro por ID
```http
GET /api/v1/books/0
```

**Response:**
```json
{
  "title": "A Light in the Attic",
  "price": "£51.77",
  "category": "Poetry",
  "availability": "In stock (22 available)",
  "rating": "Three",
  "description": "It's hard to imagine a world without A Light in the Attic. This now-classic collection of poetry and drawings from Shel Silverstein celebrates its 20th anniversary with this special edition."
}
```

**Response (Não encontrado):**
```json
{
  "detail": "Book item not found"
}
```

### **Sistema Endpoints**

#### 8. Health Check
```http
GET /api/v1/health
```

**Response:**
```json
{
  "api_status": "online",
  "uptime_seconds": 3661.45,
  "scraping_status": "Scraping concluído com sucesso. 1000 livros coletados.",
  "books_scraped": 1000,
  "csv_file_size_mb": 2.456,
  "csv_creation_date": "2025-11-01 14:30:15"
}
```

**Response (Scraping em andamento):**
```json
{
  "api_status": "online",
  "uptime_seconds": 1234.56,
  "scraping_status": "Scraping em execução. 450 livros coletados até agora.",
  "books_scraped": 450,
  "csv_file_size_mb": 1.234,
  "csv_creation_date": "2025-11-01 14:00:00"
}
```

**Response (Scraping não iniciado):**
```json
{
  "api_status": "online",
  "uptime_seconds": 567.89,
  "scraping_status": "Scraping não foi iniciado ainda.",
  "books_scraped": null,
  "csv_file_size_mb": null,
  "csv_creation_date": null
}
```

---

## Exemplos de Uso com cURL

### Iniciar Scraping
```bash
curl -X GET "http://localhost:8001/api/v1/scraper/start" \
     -H "accept: application/json"
```

### Buscar Livros de Ficção
```bash
curl -X GET "http://localhost:8001/api/v1/books/search?category=Fiction" \
     -H "accept: application/json"
```

### Listar Categorias
```bash
curl -X GET "http://localhost:8001/api/v1/books/categories" \
     -H "accept: application/json"
```

### Obter Status
```bash
curl -X GET "http://localhost:8001/api/v1/scraper/status" \
     -H "accept: application/json"
```

### Health Check
```bash
curl -X GET "http://localhost:8001/api/v1/health" \
     -H "accept: application/json"
```

---

## 🔗 Exemplos de Uso com Python Requests

```python
import requests

# Base URL da API
BASE_URL = "http://localhost:8001"

# 1. Iniciar scraping
response = requests.get(f"{BASE_URL}/api/v1/scraper/start")
print(response.json())

# 2. Verificar status
response = requests.get(f"{BASE_URL}/api/v1/scraper/status")
print(response.json())

# 3. Buscar livros por categoria
response = requests.get(f"{BASE_URL}/api/v1/books/search", 
                       params={"category": "Fiction"})
print(response.json())

# 4. Obter livro específico
response = requests.get(f"{BASE_URL}/api/v1/books/0")
print(response.json())

# 5. Listar categorias
response = requests.get(f"{BASE_URL}/api/v1/books/categories")
print(response.json())

# 6. Health check
response = requests.get(f"{BASE_URL}/api/v1/health")
print(response.json())
```

---

## Estrutura de Dados

### Campos dos Livros
Cada livro coletado contém os seguintes campos:

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `title` | string | Título do livro | "A Light in the Attic" |
| `price` | string | Preço formatado | "£51.77" |
| `category` | string | Categoria do livro | "Poetry" |
| `availability` | string | Status de disponibilidade | "In stock (22 available)" |
| `rating` | string | Avaliação em palavras | "Three" |
| `description` | string | Descrição completa | "It's hard to imagine..." |

### Estados do Scraping
O processo de scraping pode estar nos seguintes estados:

| Estado | Descrição |
|--------|-----------|
| `Idle` | Processo parado, pronto para iniciar |
| `Running` | Coletando dados em background |
| `Stopping` | Parando o processo atual |
| `Done` | Scraping concluído com sucesso |
| `Error` | Erro durante o processo |

---

## Deploy em Produção

### Deploy no Render

A aplicação está configurada para deploy automático no Render com suporte a variáveis de ambiente:

1. **Conecte o repositório** ao Render
2. **Configure as seguintes opções:**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `./` (raiz do repositório)

3. **Variáveis de ambiente** (opcional):
   - **HOST**: `0.0.0.0` (padrão, aceita conexões externas)
   - **PORT**: `8001` (padrão)

4. **Acesse a aplicação** no URL fornecido pelo Render

### Exemplo de URL de Produção
- **API**: https://tech-challenge-1-r7gr.onrender.com
- **Documentação**: https://tech-challenge-1-r7gr.onrender.com/docs
- **Health Check**: https://tech-challenge-1-r7gr.onrender.com/api/v1/health
---


### Configuração de Armazenamento
O arquivo CSV é salvo em `./data/scraping_books_database.csv` automaticamente quando o scraping é executado. Para alterar o local, edite a variável `SCRAPING_DATABASE_FILE` em `services/web_scraper.py`.

---

## Suporte

Para suporte e dúvidas:
- Email: gabriel.wensev@gmail.com
- Documentação: http://localhost:8001/docs
- Issues: Abra uma issue no repositório

---
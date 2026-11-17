
# Samsung Phone Query & Review System

An end-to-end intelligent smartphone information and review generation system that scrapes Samsung smartphone specifications from GSMArena, stores structured data in PostgreSQL, answers natural-language questions using Retrieval-Augmented Generation (RAG), generates detailed product reviews through a CrewAI multi-agent pipeline, and exposes all functionalities through a FastAPI service.

## Project Status

| Component | Status | Evidence |
|---|---|---|
| Web Scraper (GSMArena) | Completed | `scraper.py` |
| PostgreSQL Database | Completed | `db.py`, `rag_schema.py` |
| RAG Chatbot | Completed | `rag_chat.py` |
| CrewAI Multi-Agent System | Completed | `agents.py`, `crew_runner.py` |
| FastAPI Service | Completed | `main.py` |

## System Architecture

![Architecture Diagram](architecture_v2.png)

The system follows a modular architecture consisting of five major components:

1. **Data Collection:** Scrapes Samsung smartphone specifications from GSMArena using Requests and BeautifulSoup4.
2. **Database Management:** Stores smartphone information, specifications, and structured features in PostgreSQL with pgvector support.
3. **Retrieval-Augmented Generation (RAG):** Converts natural-language questions into embeddings, retrieves relevant smartphone information, and generates contextual answers using an LLM.
4. **Multi-Agent Review Generation:** Uses CrewAI agents to analyze smartphone specifications and generate comprehensive product reviews.
5. **REST API:** Provides endpoints through FastAPI for accessing phone data, asking questions, and generating reviews.

## Tech Stack

| Category | Technology |
|---|---|
| Programming Language | Python 3.12 |
| Web Scraping | Requests, BeautifulSoup4 |
| Database | PostgreSQL 18 |
| Vector Database | pgvector 0.8.7 |
| ORM | SQLAlchemy 2.1 |
| Data Modeling | SQLAlchemy Typed Mapped[] |
| Embedding Model | sentence-transformers/all-MiniLM-L6-v2 |
| Embedding Dimensions | 384 |
| LLM Provider | Groq API |
| RAG Model | openai/gpt-oss-20b |
| Review Generation Model | openai/gpt-oss-120b |
| Multi-Agent Framework | CrewAI 1.15 |
| API Framework | FastAPI |
| ASGI Server | Uvicorn |
| Database Hosting | Neon PostgreSQL (Free Tier) |

## Dataset Overview

The system currently contains information about 13 Samsung smartphones collected from GSMArena.

| Smartphone | Specification Rows | Release Year | Chipset |
|---|---:|---:|---|
| Galaxy A17 | 54 | 2025 | Exynos 1330 |
| Galaxy A26 | 55 | 2025 | Exynos 1380 |
| Galaxy A36 | 56 | 2025 | Snapdragon 6 Gen 3 |
| Galaxy A57 | 53 | 2026 | Exynos 1680 |
| Galaxy S22 5G | 57 | 2022 | Exynos 2200 / Snapdragon 8 Gen 1 |
| Galaxy S23 | 58 | 2023 | Snapdragon 8 Gen 2 |
| Galaxy S23 FE | 50 | 2023 | Exynos 2200 |
| Galaxy S23+ | 58 | 2023 | Snapdragon 8 Gen 2 |
| Galaxy S24 | 57 | 2024 | Snapdragon 8 Gen 3 |
| Galaxy S25 | 60 | 2025 | Snapdragon 8 Elite |
| Galaxy S25 Ultra | 61 | 2025 | Snapdragon 8 Elite |
| Galaxy S26 | 60 | 2026 | Snapdragon 8 Elite Gen 5 |
| Galaxy S26 Ultra | 61 | 2026 | Snapdragon 8 Elite Gen 5 |

Each smartphone also has a structured `phone_features` record containing:

- Display size and technology
- Screen resolution
- Chipset
- Operating system
- RAM and internal storage
- Main camera resolution (MP)
- Selfie camera resolution (MP)
- Battery capacity (mAh)
- Charging speed (W)
- Active-use score
- Battery endurance rating
- Device weight

**Dataset Summary:**
- Total smartphones: 13
- Total specification records: Approximately 740
- Structured feature records: 13

## Core Features

### 1. Automated Web Scraping

- Extracts Samsung smartphone specifications from GSMArena.
- Uses Requests and BeautifulSoup4 for data collection.
- Organizes scraped information into structured records.
- Supports storing smartphone specifications in PostgreSQL.

### 2. PostgreSQL Database

- Uses PostgreSQL with SQLAlchemy ORM.
- Implements relational database tables and foreign-key constraints.
- Supports vector storage through pgvector.
- Stores both detailed specifications and structured smartphone features.

### 3. Retrieval-Augmented Generation (RAG)

- Uses `all-MiniLM-L6-v2` for generating 384-dimensional embeddings.
- Retrieves relevant smartphone information from the database.
- Uses Groq-hosted LLM inference for contextual responses.
- Answers natural-language questions based on the collected dataset.

### 4. CrewAI Multi-Agent Review Generation

- Uses two specialized AI agents.
- Analyzes smartphone specifications.
- Generates structured product reviews of approximately 300¡V400 words.
- Uses Groq's `openai/gpt-oss-120b` model for review generation.

### 5. FastAPI REST Service

The application exposes the following endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks application health |
| GET | `/phones` | Retrieves available Samsung smartphones |
| POST | `/ask` | Answers natural-language smartphone queries |
| POST | `/review` | Generates AI-powered smartphone reviews |

## Project Structure

```text
Samsung-Phones-Query-and-Review-System/
¢x
¢u¢w¢w scraper.py
¢u¢w¢w db.py
¢u¢w¢w rag_schema.py
¢u¢w¢w rag_chat.py
¢u¢w¢w agents.py
¢u¢w¢w crew_runner.py
¢u¢w¢w main.py
¢u¢w¢w seed_from_csv.py
¢u¢w¢w embed_specs.py
¢x
¢u¢w¢w data/
¢x   ¢|¢w¢w seed/
¢x       ¢|¢w¢w CSV data exports
¢x
¢u¢w¢w requirements.txt
¢u¢w¢w .env
¢u¢w¢w .gitignore
¢|¢w¢w README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Samsung-Phones-Query-and-Review-System
```

### 2. Create a Virtual Environment

```bash
python3.12 -m venv .venv
```

### 3. Activate the Virtual Environment

**macOS / Linux:**

```bash
source .venv/bin/activate
```

**Windows:**

```bash
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project root directory:

```env
DATABASE_URL=postgresql+psycopg://username:password@host:5432/database_name
GROQ_API_KEY=your_groq_api_key
```

Replace the placeholder values with your actual PostgreSQL connection string and Groq API key.

**Note:** Never commit your `.env` file or expose API credentials in a public repository.

### 6. Initialize the Database

You can rebuild the database structure and load the existing smartphone data using the provided CSV exports:

```bash
python db.py
python rag_schema.py
python seed_from_csv.py
python embed_specs.py
```

Alternatively, run the scraper to collect fresh smartphone specifications directly from GSMArena:

```bash
python scraper.py
```

**Note:** Run the database initialization and data-loading scripts in the order required by their implementation. The CSV seeding and embedding scripts depend on the corresponding database tables and data.

### 7. Start the FastAPI Server

```bash
uvicorn main:app --reload
```

The API will be available at:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

Alternative API documentation:

`http://127.0.0.1:8000/redoc`

## Example API Usage

### Check Application Health

```http
GET /health
```

### Retrieve Samsung Smartphones

```http
GET /phones
```

### Ask a Natural-Language Question

```http
POST /ask
Content-Type: application/json
```

Example request:

```json
{
  "query": "Which Samsung smartphone has the best battery capacity?"
}
```

### Generate a Smartphone Review

```http
POST /review
Content-Type: application/json
```

Example request:

```json
{
  "phone_name": "Samsung Galaxy S25 Ultra"
}
```

**Note:** Example request fields should match the Pydantic request schemas implemented in `main.py`.

## Testing and Verification

The following components have been implemented and tested:

- Web scraper successfully collected data for 13 Samsung smartphones.
- PostgreSQL database contains five tables with relational constraints and pgvector support.
- RAG chatbot successfully verified against three sample task queries.
- CrewAI pipeline generated product reviews of approximately 300¡V400 words using two agents.
- FastAPI service provides health-check, smartphone retrieval, question-answering, and review-generation endpoints.

## Future Improvements

- Expand the smartphone dataset to include additional Samsung models.
- Implement automated scraping schedules and incremental database updates.
- Improve RAG retrieval accuracy through hybrid search and reranking.
- Add source citations and specification references to chatbot responses.
- Introduce review evaluation and factual consistency checks.
- Develop a frontend dashboard for interacting with the system.
- Add authentication, request validation, and API rate limiting.
- Implement automated unit and integration testing.
- Add Docker support for easier deployment.
- Deploy the application with production-ready configuration.

## Disclaimer

This project is developed for educational and research purposes. Smartphone specifications are collected from GSMArena. All product names, trademarks, and related content belong to their respective owners.

The accuracy of generated answers and reviews depends on the quality of the collected data and the underlying language models.

## Author

**Md. Shadman Hasin**

Computer Science & Engineering Graduate | Software Developer & IT Professional

- LinkedIn: [linkedin.com/in/md-shadman-hasin](https://linkedin.com/in/md-shadman-hasin)
- GitHub: [github.com/Hasin-99](https://github.com/Hasin-99)
- Portfolio: [hasin-portfolio.onrender.com](https://hasin-portfolio.onrender.com)

---

**Built with Python, PostgreSQL, RAG, CrewAI, and FastAPI.**

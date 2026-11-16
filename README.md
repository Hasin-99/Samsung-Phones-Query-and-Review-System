# Samsung Phone Query & Review System

An end-to-end intelligent system that scrapes Samsung smartphone data from GSMArena, stores it in PostgreSQL, answers natural-language questions via RAG, generates product reviews via a CrewAI multi-agent pipeline, and exposes everything through a FastAPI service.

## Project Status

| Component | Status | Evidence |
|---|---|---|
| Web scraper (GSMArena) | OK - 13 phones, ~740 spec rows | `scraper.py` |
| PostgreSQL database | OK - 5 tables, foreign keys, pgvector | `db.py`, `rag_schema.py` |
| RAG chatbot | OK - 3/3 sample task queries verified | `rag_chat.py` |
| CrewAI multi-agent | OK - 2 agents, 300-400 word reviews | `agents.py`, `crew_runner.py` |
| FastAPI | OK - /health, /phones, /ask, /review | `main.py` |

## Architecture

GSMArena --> scraper.py --> PostgreSQL (Neon)
(BS4) |
+-- phones
+-- specifications --> embed_specs.py
+-- phone_features (all-MiniLM-L6-v2)
+-- prices |
+-- spec_chunks <-------------+
(740 vectors)
|
+----------------+----------------+
| |
v v
rag_chat.py crew_runner.py
(RAG + Groq) (CrewAI agents)
| |
| "What is the camera | Agent 1: Spec Retriever
| of the Galaxy S23?" | Agent 2: Review Writer
| |
+----------------+----------------+
|
v
main.py
(FastAPI)
|
+----------------+----------------+
v v v
/ask /review /phones

## Tech Stack

- Scraping: requests, BeautifulSoup4
- Database: PostgreSQL 18 (Neon free tier) + pgvector 0.8.7
- ORM: SQLAlchemy 2.1 with typed Mapped[] models
- Embeddings: sentence-transformers/all-MiniLM-L6-v2 (384-dim, runs locally)
- LLM: Groq API, openai/gpt-oss-20b (RAG) and openai/gpt-oss-120b (reviews)
- Multi-agent: CrewAI 1.15
- API: FastAPI + uvicorn

## Data Summary

13 Samsung phones scraped from GSMArena:

| Phone | Spec rows | Release | Chipset |
|---|---|---|---|
| Galaxy A17 | 54 | 2025 | Exynos 1330 |
| Galaxy A26 | 55 | 2025 | Exynos 1380 |
| Galaxy A36 | 56 | 2025 | Snapdragon 6 Gen 3 |
| Galaxy A57 | 53 | 2026 | Exynos 1680 |
| Galaxy S22 5G | 57 | 2022 | Exynos 2200 / SD 8 Gen 1 |
| Galaxy S23 | 58 | 2023 | Snapdragon 8 Gen 2 |
| Galaxy S23 FE | 50 | 2023 | Exynos 2200 |
| Galaxy S23+ | 58 | 2023 | Snapdragon 8 Gen 2 |
| Galaxy S24 | 57 | 2024 | Snapdragon 8 Gen 3 |
| Galaxy S25 | 60 | 2025 | Snapdragon 8 Elite |
| Galaxy S25 Ultra | 61 | 2025 | Snapdragon 8 Elite |
| Galaxy S26 | 60 | 2026 | Snapdragon 8 Elite Gen 5 |
| Galaxy S26 Ultra | 61 | 2026 | Snapdragon 8 Elite Gen 5 |

Each phone also has a structured `phone_features` row: display size/type, resolution, chipset, OS, RAM, storage, camera MP, selfie MP, battery mAh, charging W, active-use score, endurance rating, weight.

## Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd Samsung-Phones-Query-and-Review-System
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
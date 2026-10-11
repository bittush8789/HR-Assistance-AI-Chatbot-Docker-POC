<div align="center">

# 🤖 HR Assistance AI Chatbot (Docker POC)

**A production-ready Proof of Concept (POC) for an enterprise HR Chatbot using FastAPI, LangChain RAG, OpenAI GPT-4o mini, and persistent ChromaDB vector storage.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white)](https://openai.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6F61)](https://www.trychroma.com/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

[Quick Start](#-quick-start) • [Architecture](#-architecture--workflow) • [Docker & Docker Compose](#-docker--docker-compose) • [Push to Docker Hub](#-push-to-docker-hub-step-by-step) • [API Reference](#-api-endpoints--testing) • [Documentation Guide](docs/STEP_BY_STEP_GUIDE.md)

</div>

---

## 📌 Overview

The **HR Assistance AI Chatbot** enables employees to query company HR policies and receive accurate, grounded responses with exact source citations.

- **Grounded Responses**: Answers are strictly generated from predefined HR policies in `data/documents/`.
- **Anti-Hallucination Guardrails**: If a question is out of scope or details are missing, the bot returns a clear fallback response rather than inventing company policies.
- **Persistent Vector Store**: Uses ChromaDB mounted on a persistent volume so embeddings are retained across container reboots without paying for duplicate embedding API calls.
- **Zero Document Uploads**: Operates in a secured, closed policy environment without user-uploaded files.

---

## ⚡ Quick Start (30 Seconds)

```bash
# 1. Clone or enter the repository
cd hr-assistant-poc

# 2. Configure environment credentials
cp .env.example .env
# Edit .env and paste your OPENAI_API_KEY

# 3. Start the container with Docker Compose
docker compose up -d

# 4. Check application health
curl http://localhost:8000/health
```

Access the interactive API documentation at **`http://localhost:8000/docs`**.

---

## 🏗️ Architecture & Workflow

```mermaid
flowchart TD
    subgraph Client["Employee / Client"]
        UserReq["HTTP POST /chat<br/>{question}"]
    end

    subgraph Container["Docker Container (:8000)"]
        FastAPI["FastAPI Application (Uvicorn)"]
        RAG["LangChain RAG Pipeline"]
        Prompt["Strict Anti-Hallucination Prompt"]
        VectorDB[("ChromaDB Persistent Store<br/>/app/data/chroma_db")]
        Docs[("HR Policy Documents<br/>/app/data/documents")]
    end

    subgraph External["External Cloud APIs"]
        EmbedAPI["OpenAI text-embedding-3-small"]
        LLMAPI["OpenAI GPT-4o mini"]
    end

    UserReq --> FastAPI
    FastAPI --> RAG
    RAG -->|Similarity Search| VectorDB
    Docs -.->|One-time Indexing| EmbedAPI
    EmbedAPI -.->|Vector Embeddings| VectorDB
    VectorDB -->|Top-K Policy Chunks| RAG
    RAG --> Prompt
    Prompt --> LLMAPI
    LLMAPI -->|Grounded Answer| FastAPI
    FastAPI -->|JSON {answer, sources}| UserReq
```

---

## 📂 Project Structure

```text
hr-assistant-poc/
├── app/
│   ├── __init__.py           # Application package
│   ├── config.py             # Pydantic BaseSettings & path configuration
│   ├── main.py               # FastAPI routes, schemas, lifecycle & error handlers
│   └── rag.py                # LangChain RAG pipeline & ChromaDB manager
├── data/
│   ├── documents/            # Predefined sample HR policies
│   │   ├── leave_policy.txt
│   │   ├── work_from_home.txt
│   │   ├── expense_policy.txt
│   │   └── employee_benefits.txt
│   └── chroma_db/            # Persistent ChromaDB vector storage (.gitkeep)
├── docs/
│   └── STEP_BY_STEP_GUIDE.md # Detailed deployment & Docker Hub push guide
├── tests/
│   ├── __init__.py
│   └── test_app.py           # Automated test suite (8 passing unit tests)
├── Dockerfile                # Python 3.12-slim container image
├── docker-compose.yml        # Orchestration with persistent volume mounts
├── requirements.txt          # Pinned Python package dependencies
├── .env.example              # Template environment file
├── .env                      # Local runtime environment file (gitignored)
├── .dockerignore             # Excludes cache, secrets, and local storage from Docker build
├── .gitignore                # Excludes secrets, venv, and local database files
└── README.md                 # Complete documentation and developer guide
```

---

## 💻 Local Development (Without Docker)

### 1. Create a Python Virtual Environment
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure `.env`
```bash
cp .env.example .env
```
Edit `.env`:
```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### 4. Run Locally
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run Automated Tests
```bash
pytest tests/ -v
```

---

## 🐳 Docker & Docker Compose

### Step 1: Build the Docker Image
```bash
docker compose build
# Or standalone: docker build -t hr-assistant-poc:latest .
```

### Step 2: Start the Service
```bash
docker compose up -d
```

### Step 3: View Container Logs
```bash
docker compose logs -f hr-assistant
```

### Step 4: Stop the Service
```bash
docker compose down
```

---

## 🚀 Push to Docker Hub (Step-by-Step)

Follow these steps to package and push your container image to **Docker Hub**:

### 1. Log in to Docker Hub
```bash
docker login
```
*Enter your Docker Hub username and password (or Personal Access Token).*

### 2. Tag Your Image
Tag the local image with your Docker Hub username and repository name:

```bash
# Format: docker tag <local-image> <dockerhub-username>/<repo-name>:<tag>
docker tag hr-assistant-poc:latest <your-dockerhub-username>/hr-assistant-poc:latest
docker tag hr-assistant-poc:latest <your-dockerhub-username>/hr-assistant-poc:1.0.0
```

*Example:*
```bash
docker tag hr-assistant-poc:latest alexdevops/hr-assistant-poc:latest
docker tag hr-assistant-poc:latest alexdevops/hr-assistant-poc:1.0.0
```

### 3. Push to Docker Hub
```bash
docker push <your-dockerhub-username>/hr-assistant-poc:latest
docker push <your-dockerhub-username>/hr-assistant-poc:1.0.0
```

### 4. Pull and Run on Any Host
Anyone can pull and run your published image:

```bash
# 1. Create .env with OPENAI_API_KEY
echo "OPENAI_API_KEY=sk-your-key" > .env

# 2. Run container with persistent ChromaDB volume
docker run -d \
  --name hr-assistant-app \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/data/chroma_db:/app/data/chroma_db" \
  <your-dockerhub-username>/hr-assistant-poc:latest
```

> 📖 **Need a complete walkthrough?** See the full [Docker & Docker Hub Deployment Guide](docs/STEP_BY_STEP_GUIDE.md).

---

## 📡 API Endpoints & Testing

### 1. Health Check (`GET /health`)
Verify API status, OpenAI configuration, and indexed chunk count:

```bash
curl -X GET "http://localhost:8000/health"
```

**Response (`200 OK`):**
```json
{
  "status": "healthy",
  "openai_configured": true,
  "model": "gpt-4o-mini",
  "embedding_model": "text-embedding-3-small",
  "vector_store": "ready",
  "indexed_chunks": 12
}
```

---

### 2. Index Documents (`POST /index`)
Indexes predefined HR policies into ChromaDB. Skips if already indexed to save API cost.

```bash
# Standard index
curl -X POST "http://localhost:8000/index" \
     -H "Content-Type: application/json" \
     -d '{}'

# Force rebuild
curl -X POST "http://localhost:8000/index" \
     -H "Content-Type: application/json" \
     -d '{"force": true}'
```

---

### 3. Ask HR Questions (`POST /chat`)

#### Example A: Leave Policy Query
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the annual leave policy?"}'
```

**Response:**
```json
{
  "question": "What is the annual leave policy?",
  "answer": "Full-time regular employees accrue 20 paid annual leave days per calendar year (approximately 1.67 days per full month worked). A maximum of 5 unused annual leave days can be carried over into the following calendar year, which must be used by March 31st.",
  "sources": [
    "leave_policy.txt"
  ]
}
```

#### Example B: Work From Home & Equipment
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"question": "How much stipend do I get for home office setup?"}'
```

**Response:**
```json
{
  "question": "How much stipend do I get for home office setup?",
  "answer": "Eligible employees receive a one-time, non-taxable home office setup stipend of $500 USD for ergonomic workspace equipment.",
  "sources": [
    "work_from_home.txt"
  ]
}
```

#### Example C: Travel & Expense Allowance
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the daily meal allowance during business travel?"}'
```

**Response:**
```json
{
  "question": "What is the daily meal allowance during business travel?",
  "answer": "The daily meal reimbursement during business travel is capped at $75 USD per day, broken down into Breakfast ($15 USD), Lunch ($25 USD), and Dinner ($35 USD).",
  "sources": [
    "expense_policy.txt"
  ]
}
```

#### Example D: Out-of-Scope Fallback (Anti-Hallucination)
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"question": "How do I bake a chocolate cake?"}'
```

**Response:**
```json
{
  "question": "How do I bake a chocolate cake?",
  "answer": "I'm sorry, but the available HR policy documents do not contain sufficient information to answer this question. Please reach out to the HR department at hr@company.local for further assistance.",
  "sources": []
}
```

---

## 🛡️ Error Handling & Status Codes

| Scenario | HTTP Status Code | Behavior |
| :--- | :--- | :--- |
| **Missing OpenAI API Key** | `503 Service Unavailable` | Returns descriptive error without exposing internal secrets |
| **Empty Question** | `400 Bad Request` | Pydantic validation rejects whitespace/empty input |
| **Unrelated Question** | `200 OK` | Polite fallback response with empty source array `[]` |
| **OpenAI API Outage** | `502 Bad Gateway` | Gracefully catches API connection errors |
| **ChromaDB Error** | `500 Internal Server Error` | Logs internal exception, returns clean user message |

---

## 🔒 Security Best Practices

1. **No Hardcoded Keys**: API credentials are loaded dynamically from environment variables at runtime.
2. **Build Context Exclusions**: `.env` and local database files are excluded via `.dockerignore`.
3. **Slim Base Image**: Uses `python:3.12-slim` to minimize vulnerability exposure.
4. **Volume Mount Persistence**: Vector index data is decoupled from container lifecycle using Docker volume mounts.

---

## 📚 Detailed Documentation

For advanced deployment instructions, multi-architecture builds, and troubleshooting tips, see:
- 📖 [Comprehensive Step-by-Step Guide](docs/STEP_BY_STEP_GUIDE.md)

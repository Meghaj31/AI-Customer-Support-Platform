# AI Customer Support Platform

A multi-tenant RAG backend: companies upload their documentation as PDFs, and their customers chat with an LLM that answers from those documents only.

**Live API docs:** `https://YOUR-APP.up.railway.app/docs` · **Repository:** `https://github.com/YOUR-USERNAME/AI-Customer-Support-Platform`

---

## Overview

Each company registers, uploads PDF documentation, and gets its own isolated knowledge base. When a customer asks a question, the system embeds it, retrieves the most semantically similar chunks from **that company's documents only**, and sends them to an LLM with instructions to answer strictly from that context. If the model can't answer from the documentation, the reply is flagged `escalated` so a human can step in.

This repository is the backend (FastAPI). A web frontend is not part of this repo yet.

## Key Features

- **Retrieval-Augmented Generation** over uploaded PDFs: extraction, overlapping chunking, local embeddings, vector search, grounded generation
- **Semantic search in PostgreSQL** with pgvector (cosine distance), with no separate vector database
- **Multi-tenant by design**: every document, chunk, and conversation belongs to a company, and the company is derived from the JWT, never from request input
- **JWT authentication** (OAuth2 password flow, bcrypt-hashed passwords)
- **Conversation memory**: prior messages are replayed to the model on each turn
- **Escalation flag** on answers the model could not ground in the documentation
- **Layered architecture** (Router → Service → Repository) with async SQLAlchemy and Alembic migrations
- **Containerized** with Docker and deployed on Railway

## Architecture

```mermaid
flowchart LR
    Client[Client / Swagger UI] -->|HTTPS + JWT| R[Routers<br/>auth · documents · chat]
    R --> S[Services<br/>business logic]
    S --> Repo[Repositories<br/>DB queries only]
    Repo --> DB[(PostgreSQL + pgvector)]
    S --> E[Embedding service<br/>sentence-transformers]
    S --> L[Groq LLM<br/>via LangChain]
```

| Layer | Responsibility |
|---|---|
| **Router** (`app/routers/`) | HTTP only: parse requests, call a service, shape the response |
| **Service** (`app/services/`) | Business logic and orchestration, including ownership checks (404/403) |
| **Repository** (`app/repositories/`) | Database queries only, with no HTTP or business rules |

## How It Works

### 1. Document ingestion (`POST /documents/`)

1. The PDF is read into memory and text is extracted page by page with `pypdf`.
2. A `Document` row is created first, so chunks can reference its ID.
3. Text is split into **500-word chunks with a 50-word overlap**, so sentences cut at a boundary still appear whole in at least one chunk.
4. Every chunk is embedded with `all-MiniLM-L6-v2` (**384 dimensions**) in a single batched call.
5. `DocumentChunk` rows (text + embedding + `document_id` + `company_id`) are saved in one `add_all`.

### 2. Answering a question (`POST /chat/conversations/{id}/messages`)

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant DB as PostgreSQL/pgvector
    participant LLM as Groq LLM
    C->>API: question (JWT)
    API->>DB: save user message
    API->>DB: load conversation history
    API->>API: embed question (same model as documents)
    API->>DB: top-5 chunks by cosine distance WHERE company_id = caller
    API->>LLM: system prompt + retrieved context + history + question
    LLM-->>API: answer
    API->>API: escalation check
    API->>DB: save assistant message (escalated flag)
    API-->>C: assistant message
```

### 3. Keeping answers grounded

- The system prompt instructs the model to answer **only** from the retrieved documentation and to reply with a fixed fallback sentence when the answer isn't there.
- Retrieved chunks are the only knowledge injected into the prompt, and retrieval is filtered by the caller's `company_id`.
- Answers containing "I don't know" or "I'm not sure" set `escalated = true` (see [Limitations](#limitations)).
- The user's message is saved **before** generation, so a failed LLM call still leaves a record of the question.

## Tech Stack

| Area | Technology |
|---|---|
| API | FastAPI, Pydantic v2, pydantic-settings |
| Database | PostgreSQL 16 + pgvector, SQLAlchemy 2 (async, asyncpg), Alembic |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2`, run locally on CPU (no API calls) |
| LLM | Groq API through LangChain (`langchain-groq`), model `openai/gpt-oss-20b` |
| PDF parsing | pypdf |
| Auth | python-jose (JWT), passlib + bcrypt |
| Packaging / hosting | Docker, Railway (app + pgvector Postgres) |

## Project Structure

```
AI-Customer-Support-Platform/
├── app/
│   ├── routers/          # auth.py, documents.py, chat.py
│   ├── services/         # auth_service.py, embedding_service.py,
│   │                     # document_service.py, chat_service.py
│   ├── repositories/     # document_repo.py, chat_repo.py
│   ├── models/           # Company, Document, DocumentChunk, Conversation, Message
│   ├── schemas/          # Pydantic request/response models
│   ├── config.py         # settings loaded from environment / .env
│   ├── database.py       # async engine, session, Base, get_db
│   └── main.py           # app creation, router registration, /health
├── alembic/              # migrations
├── Dockerfile
├── docker-compose.yml    # pgvector Postgres (+ app)
├── init.sql              # CREATE EXTENSION vector
├── requirements.txt
└── .env.example
```

## Database Design

```mermaid
erDiagram
    COMPANY ||--o{ DOCUMENT : owns
    COMPANY ||--o{ CONVERSATION : owns
    COMPANY ||--o{ DOCUMENT_CHUNK : owns
    DOCUMENT ||--o{ DOCUMENT_CHUNK : "split into"
    CONVERSATION ||--o{ MESSAGE : contains

    COMPANY { uuid id string name string email string hashed_password }
    DOCUMENT { uuid id uuid company_id string filename datetime created_at }
    DOCUMENT_CHUNK { uuid id uuid document_id uuid company_id text content vector_384 embedding datetime created_at }
    CONVERSATION { uuid id uuid company_id datetime created_at }
    MESSAGE { uuid id uuid conversation_id enum role text content bool escalated datetime created_at }
```

`DocumentChunk` stores `company_id` directly, in addition to its link through `Document`. Retrieval filters on it without a join. Deleting a document cascades to its chunks.

## API Endpoints

All endpoints except register, login, and health require `Authorization: Bearer <token>`.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/auth/register` | Register a company (`name`, `email`, `password`) |
| `POST` | `/auth/login` | Log in (OAuth2 form: `username` = email, `password`), returns a JWT |
| `POST` | `/documents/` | Upload a PDF (multipart), then extract, chunk, embed, store |
| `GET` | `/documents/` | List the caller's documents |
| `DELETE` | `/documents/{document_id}` | Delete a document and its chunks (204) |
| `POST` | `/chat/conversations` | Start a conversation |
| `GET` | `/chat/conversations` | List the caller's conversations |
| `POST` | `/chat/conversations/{conversation_id}/messages` | Ask a question; runs the RAG pipeline and returns the assistant message |
| `GET` | `/chat/conversations/{conversation_id}/messages` | Get conversation history, oldest first |

Interactive docs are served at `/docs`.

## Authentication and Multi-Tenancy

- Passwords are hashed with bcrypt. Login returns a signed JWT whose `sub` claim is the company ID.
- A `get_current_company` dependency decodes the token and loads the company. Invalid or expired tokens get a `401`.
- The company identity **always comes from the token**. No endpoint accepts a `company_id` from the client.
- Every list or search query filters by `company_id`: documents, conversations, and vector retrieval.
- Endpoints that take a resource ID (delete a document, read a conversation's messages) fetch the resource first, then compare ownership: **404** if it doesn't exist, **403** if it belongs to another company.

## Local Setup

Requires Python 3.11 and Docker.

```bash
git clone https://github.com/YOUR-USERNAME/AI-Customer-Support-Platform.git
cd AI-Customer-Support-Platform

python -m venv env
# Windows:      env\Scripts\activate
# macOS/Linux:  source env/bin/activate

pip install -r requirements.txt
cp .env.example .env          # then fill in the values (see below)

docker compose up -d db       # pgvector Postgres on localhost:5434, extension enabled by init.sql
alembic upgrade head          # create tables
uvicorn app.main:app --reload
```

The first request that loads the embedding model downloads it from Hugging Face. Open `http://localhost:8000/docs`.

### Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Async SQLAlchemy URL, e.g. `postgresql+asyncpg://postgres:password@localhost:5434/ai_support` |
| `SECRET_KEY` | Secret used to sign JWTs |
| `ALGORITHM` | JWT signing algorithm (`HS256`) |
| `GROQ_API_KEY` | API key from console.groq.com |

```env
# .env.example
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5434/ai_support
SECRET_KEY=change-me
ALGORITHM=HS256
GROQ_API_KEY=your-groq-api-key
```

Generate a strong secret with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. The `DATABASE_URL` must use the `postgresql+asyncpg://` prefix.

## Example Usage

```bash
BASE=http://localhost:8000

# Register and log in
curl -X POST $BASE/auth/register -H "Content-Type: application/json" \
  -d '{"name":"Acme","email":"admin@acme.com","password":"s3cret-pass"}'

TOKEN=$(curl -s -X POST $BASE/auth/login \
  -d "username=admin@acme.com&password=s3cret-pass" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Upload documentation
curl -X POST $BASE/documents/ -H "Authorization: Bearer $TOKEN" -F "file=@docs.pdf"

# Start a conversation, then ask a question
CONV=$(curl -s -X POST $BASE/chat/conversations -H "Authorization: Bearer $TOKEN" \
  | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -X POST $BASE/chat/conversations/$CONV/messages \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"content":"How do I get a refund?"}'
```

```json
{
  "id": "8010ba06-a7a5-49b1-8188-3ad984b9cca0",
  "role": "assistant",
  "content": "…answer grounded in the uploaded documentation…",
  "created_at": "2026-09-14T15:48:08.327902Z",
  "escalated": false
}
```

## Deployment

The app runs on **Railway** as a Docker service, with a **pgvector** Postgres service in the same project.

- The `Dockerfile` uses `python:3.11-slim` and installs `requirements.txt` in its own layer so dependency installs are cached. The container runs `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000`, so the schema is migrated on every start.
- Configuration comes from the platform's environment variables (`DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `GROQ_API_KEY`, plus `PORT=8000`). `.env` is never committed.
- The database needs `CREATE EXTENSION IF NOT EXISTS vector;` once, since the image ships pgvector but doesn't enable it per database. Locally, `init.sql` does this automatically.
- `requirements.txt` pins the **CPU-only** build of PyTorch via `--extra-index-url`, avoiding multi-GB CUDA downloads for a CPU-only workload.

## Design Decisions

- **pgvector instead of a separate vector database.** Documents, chunks, and tenant data live in one transactional

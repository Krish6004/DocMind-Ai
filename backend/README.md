# DocMind AI — Backend Service

High-performance, production-ready FastAPI backend foundation for **DocMind AI**.

This backend exposes RESTful APIs for the DocMind AI document intelligence and hybrid RAG system while strictly preserving and decoupling the underlying AI engine ([`src/`](file:///Users/krishgupta/Downloads/Rag_From_Scratch-main/src)).

---

## Table of Contents

- [Architecture & Design Principles](#architecture--design-principles)
- [Directory Structure](#directory-structure)
- [SQLite & Storage Architecture](#sqlite--storage-architecture)
- [Prerequisites & Installation](#prerequisites--installation)
- [Environment Configuration](#environment-configuration)
- [Running the Backend](#running-the-backend)
- [API Endpoints](#api-endpoints)
  - [Chat & RAG Completion APIs](#chat--rag-completion-apis)
  - [Document Ingestion & Management APIs](#document-ingestion--management-apis)
  - [System & Health APIs](#system--health-apis)
- [Example API Requests](#example-api-requests)
  - [1. Chat & RAG Query](#1-chat--rag-query)
  - [2. Fetch Session Chat History](#2-fetch-session-chat-history)
  - [3. Upload a Document](#3-upload-a-document)
  - [4. List Ingested Documents](#4-list-ingested-documents)
  - [5. Delete a Document](#5-delete-a-document)
- [Interactive Documentation](#interactive-documentation)
- [Centralized Logging](#centralized-logging)
- [Exception Handling & Error Envelopes](#exception-handling--error-envelopes)
- [Dependency Injection Foundation](#dependency-injection-foundation)
- [Running Unit & Integration Tests](#running-unit--integration-tests)

---

## Architecture & Design Principles

1. **Separation of Concerns**: Clean separation between HTTP routing (`api/`), business services (`services/`), database persistence (`db/`), configuration & error normalization (`core/`), schemas (`schemas/`), and dependency injection (`deps.py`).
2. **AI Engine Preservation**: The core AI modules located in [`src/`](file:///Users/krishgupta/Downloads/Rag_From_Scratch-main/src) (loaders, chunkers, embeddings, BM25, hybrid retriever, reranker, and LLM generator) remain unmodified and are consumed cleanly via service orchestrators and dependencies.
3. **Hybrid Persistence Architecture**:
   - **SQLite via SQLAlchemy**: Stores structured document metadata (`documents`) and conversational interaction records (`chat_history`).
   - **NumPy/JSON VectorStore**: Embeddings matrices (`.npz`) and chunk text mappings (`.json`) remain strictly managed in the high-performance VectorStore for exact cosine dot-product retrieval.
4. **Stateful Conversational Memory**: Optional multi-turn conversational history stored in SQLite is seamlessly passed into LLM completions without modifying underlying retrieval mathematics.
5. **API Versioning**: Every API route is version-controlled under `/api/v1` using FastAPI sub-routers.
6. **Resilience & Observability**: Standardized JSON error envelopes, custom domain exceptions, structured logging synchronized with Uvicorn, and type-safe environment configuration powered by `pydantic-settings`.

---

## Directory Structure

```text
backend/
├── README.md                           # Backend documentation and run instructions
├── __init__.py                         # Backend root package
└── app/
    ├── __init__.py                     # Application package
    ├── main.py                         # FastAPI app factory, lifespan, CORS, middleware, router mounts
    ├── api/
    │   ├── __init__.py                 # API router package
    │   ├── deps.py                     # Centralized Dependency Injection providers
    │   └── v1/
    │       ├── __init__.py             # API v1 package
    │       ├── api.py                  # API v1 router aggregator
    │       └── endpoints/
    │           ├── __init__.py         # Endpoints package
    │           ├── chat.py             # POST /chat, GET /chat/history/{session_id}
    │           ├── documents.py        # GET /documents, GET /documents/{id}, DELETE /documents/{id}
    │           ├── health.py           # GET /health health check endpoint
    │           ├── root.py             # GET / service discovery and metadata endpoint
    │           └── upload.py           # POST /upload document ingestion endpoint
    ├── core/
    │   ├── __init__.py                 # Core infrastructure package
    │   ├── config.py                   # Pydantic BaseSettings environment manager (.env)
    │   ├── errors.py                   # Custom exceptions and global HTTP/validation exception handlers
    │   └── logging.py                  # Centralized logging setup integrated with src.logger
    ├── db/
    │   ├── __init__.py                 # Database package
    │   ├── base.py                     # SQLAlchemy DeclarativeBase
    │   ├── session.py                  # Engine, SessionLocal, get_db, init_db
    │   └── models/
    │       ├── __init__.py             # Models package
    │       ├── chat.py                 # ChatHistoryModel (chat_history table)
    │       └── document.py             # DocumentModel (documents table)
    ├── schemas/
    │   ├── __init__.py                 # Pydantic schemas package
    │   ├── chat.py                     # ChatRequest, ChatResponseData, SourceChunk, LatencyMetrics
    │   ├── common.py                   # Reusable envelopes: BaseResponse, ErrorResponse, ErrorDetail
    │   ├── document.py                 # DocumentOut, DocumentListResponse, UploadResponseData, DocumentDeleteData
    │   └── health.py                   # HealthResponse, RootResponse schemas
    └── services/
        ├── __init__.py                 # Business services package
        ├── chat_service.py             # ChatService: retrieval, reranking, memory, generation, persistence
        ├── document_service.py         # DocumentService: queries, catalog management, deletion synchronization
        └── upload_service.py           # UploadService: validation, storage, ingestion, chunking, embedding, vectorstore
```

---

## SQLite & Storage Architecture

### Database Schema (SQLite)

Located by default at `data/docmind.db` (configurable via `DOCMIND_DATABASE_URL`):

#### 1. `documents` Table
Stores catalog metadata for all ingested documents:
- `id`: `VARCHAR(36)` Primary Key (UUID)
- `filename`: `VARCHAR(255)` Indexed filename
- `file_type`: `VARCHAR(32)` Format (pdf, docx, txt, md)
- `file_size`: `INTEGER` Size in bytes
- `page_count`: `INTEGER` Nullable page count
- `chunk_count`: `INTEGER` Number of chunks indexed
- `upload_timestamp`: `DATETIME` UTC timestamp of ingestion
- `file_path`: `VARCHAR(1024)` Physical filesystem path
- `status`: `VARCHAR(32)` Default `"indexed"`

#### 2. `chat_history` Table
Stores conversational interactions and retrieval metrics:
- `id`: `VARCHAR(36)` Primary Key (UUID request ID)
- `session_id`: `VARCHAR(64)` Indexed conversation session ID
- `query`: `TEXT` User query prompt
- `answer`: `TEXT` Generated answer
- `retrieved_sources`: `TEXT` JSON-serialized source citations
- `confidence_score`: `FLOAT` Retrieval confidence (0.0 - 1.0)
- `latency_ms`: `FLOAT` Total query-to-answer latency
- `created_at`: `DATETIME` Interaction timestamp

### Vector & Disk Storage
- **Uploaded Files**: Saved in `data/uploads/` with sanitized filenames.
- **Vector Store Files**: Stored in `data/store/vector_store.npz` (L2-normalized float32 embeddings) and `data/store/vector_store.json` (document chunk texts and chunk-level metadata).

---

## Prerequisites & Installation

Ensure you have Python 3.10+ installed and the repository dependencies:

```bash
# Verify Python version
python3 --version

# Install dependencies
pip install fastapi uvicorn pydantic pydantic-settings sqlalchemy python-multipart httpx pytest
```

---

## Environment Configuration

Configuration is loaded from environment variables or a `.env` file at the repository root. Pydantic's `pydantic-settings` provides automatic type-casting and validation.

### Configuration Reference

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `DOCMIND_DATABASE_URL` | `str` | `"sqlite:///./data/docmind.db"` | SQLite database connection URL |
| `DOCMIND_UPLOAD_DIR` | `Path` | `data/uploads` | Directory for raw uploaded files |
| `DOCMIND_STORE_DIR` | `Path` | `data/store` | Directory for VectorStore `.npz` and `.json` files |
| `GROQ_API_KEY` | `str | None`| `None` | API Key for Groq/OpenAI compatible LLM inference |
| `GROQ_BASE_URL` | `str` | `"https://api.groq.com/openai/v1"` | Base URL for LLM provider API |
| `GROQ_MODEL` | `str` | `"openai/gpt-oss-120b"` | Default LLM model identifier |
| `DOCMIND_MAX_UPLOAD_SIZE_BYTES` | `int` | `52428800` (50MB) | Max allowed upload size in bytes |
| `DOCMIND_PROJECT_NAME` | `str` | `"DocMind AI Backend"` | Application name displayed in docs |
| `DOCMIND_VERSION` | `str` | `"1.0.0"` | Current API version |
| `DOCMIND_ENVIRONMENT` | `str` | `"development"` | Environment (`development`, `staging`, `production`) |
| `DOCMIND_HOST` | `str` | `"0.0.0.0"` | Server host binding |
| `DOCMIND_PORT` | `int` | `8000` | Server port binding |
| `DOCMIND_CORS_ORIGINS` | `list` | `["*"]` | Allowed CORS origins |
| `DOCMIND_LOG_LEVEL` | `str` | `"INFO"` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## Running the Backend

Launch the development server with live reload:

```bash
uvicorn backend.app.main:app --reload
```

To specify custom host or port bindings via CLI:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## API Endpoints

### Chat & RAG Completion APIs

#### 1. RAG Query: `POST /api/v1/chat`
- **Summary**: Execute a grounded question-answering query against the document knowledge base.
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "query": "How does DocMind combine dense and sparse retrieval?",
    "session_id": "session_12345",
    "top_k": 5,
    "filters": {"file_type": "pdf"},
    "use_memory": true,
    "memory_window": 3
  }
  ```
- **Execution Flow**:
  1. Validates query string (1–4000 characters) and resolves session ID.
  2. Fetches recent conversation turns from SQLite `chat_history` (up to `memory_window`, default 3).
  3. Executes hybrid retrieval via `src.retriever.HybridRetriever` (Dense embeddings + BM25 with RRF).
  4. Reranks candidates via `src.reranker.CrossEncoderReranker` (ms-marco-MiniLM-L-6-v2).
  5. Assembles grounded context blocks with conversation memory and invokes `src.generator.LLMGenerator`.
  6. Computes calibrated retrieval confidence and latency telemetry breakdown.
  7. Persists turn to SQLite `chat_history` table with assigned UUID `request_id`.

#### 2. Get Session History: `GET /api/v1/chat/history/{session_id}`
- **Summary**: Retrieve chronological conversation turns, queries, answers, and source citations for a session.

---

### Document Ingestion & Management APIs

#### 1. Ingest Document: `POST /api/v1/upload` (or `/api/v1/documents/upload`)
- **Summary**: Upload, chunk, embed, and index a document.
- **Content-Type**: `multipart/form-data`
- **Supported Formats**: `.pdf`, `.docx`, `.txt`, `.md`

#### 2. List Ingested Documents: `GET /api/v1/documents`
- **Summary**: Retrieve all indexed documents with pagination (`skip`, `limit`).

#### 3. Get Document by ID: `GET /api/v1/documents/{doc_id}`
- **Summary**: Retrieve metadata for a specific document by its UUID.

#### 4. Delete Document: `DELETE /api/v1/documents/{doc_id}`
- **Summary**: Atomically removes metadata from SQLite, purges chunks from VectorStore, and deletes disk file.

---

### System & Health APIs

- **`GET /health`** and **`GET /api/v1/health`**: System liveness check, uptime, version, and component status.
- **`GET /`** and **`GET /api/v1/`**: Service discovery metadata, documentation links, and route list.

---

## Example API Requests

### 1. Chat & RAG Query
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the primary retrieval models used in DocMind AI?",
    "session_id": "session_alpha_1",
    "top_k": 3,
    "use_memory": true,
    "memory_window": 3
  }'
```

**Response (`200 OK`):**
```json
{
  "success": true,
  "message": "Answer generated successfully.",
  "data": {
    "request_id": "c1f7a049-74d2-43bb-8884-28b9816e88fa",
    "session_id": "session_alpha_1",
    "query": "What are the primary retrieval models used in DocMind AI?",
    "answer": "DocMind AI combines dense semantic retrieval using sentence-transformers/all-MiniLM-L6-v2 with sparse keyword retrieval via BM25, fusing candidates using Reciprocal Rank Fusion [Source 1].",
    "sources": [
      {
        "source_num": 1,
        "filename": "architecture.md",
        "chunk_index": 0,
        "score": 0.895421,
        "text": "DocMind AI uses hybrid retrieval combining dense all-MiniLM embeddings and BM25 sparse indices."
      }
    ],
    "confidence": {
      "score": 0.8412,
      "percentage": 84.12,
      "level": "High",
      "color": "#10b981",
      "explanation": "High confidence (84.1%). Grounded strongly by cross-encoder and dense retrieval."
    },
    "metrics": {
      "retrieval_latency_ms": 14.25,
      "reranking_latency_ms": 8.12,
      "generation_latency_ms": 182.4,
      "total_latency_ms": 208.5,
      "retrieved_chunk_count": 6,
      "reranked_chunk_count": 3
    },
    "model": "openai/gpt-oss-120b",
    "created_at": "2026-10-28T05:00:00.000000Z"
  }
}
```

### 2. Fetch Session Chat History
```bash
curl -X GET "http://localhost:8000/api/v1/chat/history/session_alpha_1"
```

### 3. Upload a Document
```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_report.pdf"
```

### 4. List Ingested Documents
```bash
curl -X GET "http://localhost:8000/api/v1/documents?skip=0&limit=10"
```

### 5. Delete a Document
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/e4b9b47e8a9341458b29fa3a19b51bf1"
```

---

## Interactive Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema (JSON)**: [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)

---

## Centralized Logging

The backend utilizes `backend.app.core.logging.setup_backend_logging()`, seamlessly binding into `src.logger` to ensure unified formatting and log rotation across both backend APIs and the AI engine.

---

## Exception Handling & Error Envelopes

All errors return a predictable, machine-readable JSON structure:

```json
{
  "success": false,
  "error": {
    "type": "validation_error",
    "message": "Query string cannot be empty or whitespace only.",
    "status_code": 422,
    "details": null,
    "timestamp": "2026-10-28T05:01:00.000000+00:00"
  }
}
```

---

## Dependency Injection Foundation

FastAPI dependencies are declared in [`backend/app/api/deps.py`](file:///Users/krishgupta/Downloads/Rag_From_Scratch-main/backend/app/api/deps.py) using `Depends`:

- `get_app_settings()`: Cached settings singleton.
- `get_database_session()`: Request-scoped SQLAlchemy session for SQLite.
- `get_vector_store()`: Persistent singleton VectorStore instance.
- `get_embedding_model()`: Cached sentence embedding model.
- `get_reranker()`: Cached cross-encoder reranker model.
- `get_retriever()`: Synchronized HybridRetriever combining VectorStore and BM25.
- `get_generator()`: LLMGenerator instance configured from settings.
- `get_document_service()`: Document lifecycle service.
- `get_upload_service()`: Ingestion and vector synchronization service.
- `get_chat_service()`: Complete RAG query execution service.

---

## Running Unit & Integration Tests

Execute the complete test suite:

```bash
# Run backend chat and RAG pipeline integration tests
pytest tests/test_backend_chat.py -v

# Run backend upload and document lifecycle tests
pytest tests/test_backend_upload.py -v

# Run backend health and infrastructure tests
pytest tests/test_backend_health.py -v

# Run entire repository test suite (187+ tests)
pytest
```

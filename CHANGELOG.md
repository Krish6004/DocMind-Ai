# Changelog

All notable changes to the **DocMind AI** codebase are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-11-12

### Added
- **DocMind AI v2.0 — Sprint 7.0: Enterprise Authentication & Multi-User Isolation:**
  - **Hybrid Storage Architecture**:
    - **MongoDB Atlas** (`mongodb+srv://...`): Securely stores User Accounts (`users`), Persistent Multi-Turn Chat Sessions (`chat_sessions`), User Settings (`user_settings`), and Token Rotations (`refresh_tokens`).
    - **SQLite & NumPy VectorStore**: Preserved strictly for document storage, chunks, BGE embeddings, BM25 indices, and retrieval metadata without modifying the RAG pipeline math.
  - **Enterprise Authentication (`backend/app/services/auth_service.py` & `endpoints/auth.py`)**:
    - Implemented bcrypt password hashing (never plaintext).
    - JWT Access Tokens (30 min) + Refresh Tokens (30 days) with HttpOnly cookie support and Authorization header Bearer parsing.
    - Endpoints: `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `POST /api/auth/refresh`, `GET /api/auth/me`.
  - **Strict Multi-Tenant Isolation**:
    - Uploads, documents, and chunk metadata tagged with `user_id`.
    - Every retrieval query strictly scopes search candidates to `user_id`.
    - Chat history and evaluation telemetry isolated per user.
  - **Frontend Multi-User UX**:
    - Added `LoginPage.tsx` and `RegisterPage.tsx` adhering to the Jet Black / Cerulean / Neon Rose design system.
    - Added `ProtectedRoute.tsx` with automatic session restore and redirection.
    - Added User Profile Avatar & Menu with Logout in `Navbar.tsx`.
    - Connected `Sidebar.tsx` and `useChatWorkspace.ts` to MongoDB Atlas chat sessions (`/api/v1/sessions`).
  - **Tests**:
    - Added `tests/test_auth_and_isolation.py` (5 tests covering bcrypt, JWT, login/register, document isolation across users, and session isolation).
    - Total test suite now at **227 passing tests**.

---

## [1.7.0] - 2026-11-11

### Added
- **Sprint 6.0: Enterprise RAG Evaluation Framework & Benchmarking System:**
  - **Evaluation Engine (`backend/app/services/evaluation_service.py`)**:
    - Implemented isolated `EvaluationService` executing in `< 15 ms` per request as a non-intrusive post-chat observer via FastAPI `BackgroundTasks`.
    - Computes full **Retrieval Metrics** (`Precision@K`, `Recall@K`, `MRR`, `DCG`, `IDCG`, `NDCG`, `Context Recall`, `Retrieval Coverage`, `Source Diversity`).
    - Computes normalized `0 -> 100` **Generation Quality Metrics** (`Grounding`, `Faithfulness`, `Citation Coverage`, `Context Utilization`, `Answer Completeness`, `Hallucination Risk`, `Source Utilization`, `Answer Length`, `Reasoning Coverage`).
    - Performs non-destructive **Citation Verification** auditing every `[Source N]` tag (`filename`, `page_number`, `chunk_index`, `chunk_text_matches`) and returning warnings without modifying generated text.
    - Tracks stage-by-stage **Performance & Token Telemetry** (`query_rewrite`, `planner`, `retrieval`, `reranking`, `generation`, `confidence`, `memory`, `evaluation`, token counts, provider, model).
  - **SQLite Evaluation Storage (`backend/app/db/models/evaluation.py`)**:
    - Added `evaluation_history` ORM table persisting retrieval, generation, citation, latency, and token metrics.
  - **Evaluation REST APIs (`backend/app/api/v1/endpoints/evaluation.py`)**:
    - `GET /api/v1/evaluation/latest`, `GET /api/v1/evaluation/history`, `GET /api/v1/evaluation/summary`, `POST /api/v1/evaluation/run`, `GET /api/v1/evaluation/export` (`csv`, `json`, `pdf`).
  - **Ground Truth Benchmark Suite (`evaluation/datasets/`)**:
    - Created `sample_questions.json` (55 queries), `expected_answers.json`, and `benchmark_config.json`.
  - **Evaluation Dashboard (`frontend/src/pages/EvaluationPage.tsx`)**:
    - Built `/evaluation` UI in Jet Black / Cerulean Blue / Neon Rose with Recharts visualizations (Line, Area, Bar, Pie, Heatmap), expandable 100-row Evaluation History table, live 55+ query benchmark trigger, and CSV/JSON/PDF report downloads.
  - **Tests & Documentation**:
    - Added `tests/test_evaluation_framework.py` and authored `EVALUATION_FRAMEWORK.md`.
- **Sprint 4.4: Adaptive Hybrid Retrieval Planner (`backend/app/services/retrieval_planner.py`)**:
  - Added `< 2 ms` query classification (`fact_lookup`, `summary`, `comparison`, `list`, `follow_up`, `code`, `multi_document`), retrieval orchestration, and right-drawer `RetrievalPlannerCard`.

---

## [1.5.0] - 2026-10-28

### Added
- **Sprint 4.3: Conversational RAG & Chat API Engine:**
  - **ChatService (`backend/app/services/chat_service.py`)**:
    - Orchestrated end-to-end question answering pipeline: Hybrid Retrieval (Dense + BM25 RRF) $\rightarrow$ Cross-Encoder Reranking $\rightarrow$ Conversation Memory $\rightarrow$ LLM Answer Generation $\rightarrow$ Confidence Calibration $\rightarrow$ SQLite Turn Persistence.
    - Added conversation memory support: Fetches configurable window (default 3–5 turns) of past turns from SQLite `chat_history` and injects them as `user` and `assistant` context blocks.
    - Implemented high-resolution latency telemetry across retrieval, reranking, generation, and total wall-clock time.
    - Integrated with `src.retrieval_v2.compute_retrieval_confidence` for explainable confidence calibration.
    - Generates unique UUID `request_id` for every interaction turn.
  - **Chat REST API Endpoints (`backend/app/api/v1/endpoints/chat.py`)**:
    - `POST /api/v1/chat`: Full grounded RAG query completion returning answer, attributed sources, calibrated confidence, latency metrics, and UUID request ID.
    - `GET /api/v1/chat/history/{session_id}`: Chronological multi-turn chat history retrieval for thread persistence.
  - **Pydantic Schemas (`backend/app/schemas/chat.py`)**:
    - Created `ChatRequest`, `ChatResponseData`, `SourceChunk`, `ConfidenceDetails`, `LatencyMetrics`, `ChatHistoryTurn`, and `ChatHistoryResponse`.
  - **Dependency Injection (`backend/app/api/deps.py`)**:
    - Added providers for `get_retriever`, `get_reranker`, `get_generator`, and `get_chat_service`.
  - **Integration Test Suite (`tests/test_backend_chat.py`)**:
    - Added 7 integration tests covering chat completion, empty query validation, SQLite persistence, multi-turn conversation memory, metadata filtering, zero-chunk fallbacks, and UUID request ID uniqueness.
  - **Documentation**:
    - Updated `backend/README.md`.
    - Authored `BACKEND_CHAT_ARCHITECTURE.md`.

---

## [1.4.0] - 2026-10-27

### Added
- **Sprint 4.2: Ingestion & Document Backend Connection:**
  - **SQLAlchemy & SQLite Storage (`backend/app/db/`)**:
    - Implemented SQLite integration (`data/docmind.db`) with declarative base in `backend.app.db.base`.
    - Created `DocumentModel` (`documents` table) storing document catalog metadata exclusively (filename, format, size, page count, chunk count, upload timestamp, file path).
    - Created `ChatHistoryModel` (`chat_history` table) storing conversation turns, queries, grounded answers, source citations, confidence scores, and latencies.
    - Strict hybrid segregation: Embeddings and vector indices remain managed exclusively within the NumPy/JSON VectorStore (`.npz` and `.json`).
  - **Business Services (`backend/app/services/`)**:
    - `UploadService`: Validates format, enforces size limits, saves to `data/uploads/`, dispatches `src.ingestion.load_document`, splits chunks via `src.chunker.RecursiveTextChunker`, generates embeddings via `src.embeddings.EmbeddingModel`, updates VectorStore, and persists metadata in SQLite.
    - `DocumentService`: Manages catalog listing, pagination, single-document retrieval by UUID, and coordinated document deletion (SQLite row deletion, VectorStore chunk purging via `delete_by_filename()`, and disk file deletion).
  - **REST API Endpoints (`backend/app/api/v1/endpoints/`)**:
    - `POST /api/v1/upload` (and alias `/api/v1/documents/upload`): Form-data file ingestion and vector indexing.
    - `GET /api/v1/documents`: Paginated document catalog listing.
    - `GET /api/v1/documents/{doc_id}`: Document retrieval by UUID.
    - `DELETE /api/v1/documents/{doc_id}`: Atomic document and vector chunk deletion.
  - **Pydantic Schemas (`backend/app/schemas/document.py`)**:
    - Created `DocumentOut`, `DocumentListResponse`, `UploadResponseData`, and `DocumentDeleteData`.
  - **Dependency Injection (`backend/app/api/deps.py`)**:
    - Added `get_database_session`, `get_document_service`, and `get_upload_service`.
  - **Integration Test Suite (`tests/test_backend_upload.py`)**:
    - Added 11 integration tests covering upload, validation, listing, retrieval, deletion, and SQLite metadata persistence.
  - **Documentation**:
    - Updated `backend/README.md`.
    - Authored `BACKEND_UPLOAD_ARCHITECTURE.md`.

---

## [1.3.0] - 2026-10-27

### Added
- **FastAPI Backend Foundation (`backend/`):**
  - **Application Core (`backend/app/main.py`)**: Application factory pattern (`create_application()`), `lifespan` async context manager for startup/shutdown telemetry and logging, dynamic CORS configuration, global exception handler registration, top-level routes (`/`, `/health`), and `/api/v1` router aggregator.
  - **Configuration Management (`backend/app/core/config.py`)**: Type-safe environment variable management using `pydantic-settings` (`BaseSettings`, `SettingsConfigDict`), `.env` file loading, dynamic CORS origin parsing (JSON array or comma-delimited), and cached `get_settings()` dependency.
  - **Centralized Logging (`backend/app/core/logging.py`)**: Seamless bridge integrating backend and Uvicorn loggers with `src.logger.configure_logging`.
  - **Error Normalization & Domain Exceptions (`backend/app/core/errors.py`)**: Custom exceptions (`DocMindAPIException`, `ResourceNotFoundException`, `ValidationException`, `ServiceUnavailableException`), and structured handlers for `DocMindAPIException`, `RequestValidationError`, `StarletteHTTPException`, `HTTPException`, and unhandled 500 exceptions returning a standardized JSON error envelope.
  - **Pydantic Schemas (`backend/app/schemas/`)**: Generic `BaseResponse[T]`, `ErrorResponse`, `ErrorDetail`, `HealthResponse`, `SystemStatus`, and `RootResponse` models with full OpenAPI 3.1.0 schema compliance.
  - **Dependency Injection Foundation (`backend/app/api/deps.py`)**: Decoupled injection providers for `Settings`, request logger, and forward-compatible factory stubs for `VectorStore`, `HybridRetriever`, and `LLMGenerator`.
  - **API Endpoints (`backend/app/api/v1/endpoints/`)**:
    - `GET /health` and `GET /api/v1/health`: System health status, version, uptime, and service readiness.
    - `GET /` and `GET /api/v1/`: Service discovery, version, environment, and documentation links.
  - **Interactive Documentation**: Swagger UI at `/docs`, ReDoc at `/redoc`, and OpenAPI JSON specification at `/api/v1/openapi.json`.
  - **Architectural Documentation**: Created `backend/README.md` and `BACKEND_ARCHITECTURE.md`.
  - **Unit Test Suite (`tests/test_backend_health.py`)**: Added 11 unit tests covering health checks, root metadata, Swagger/ReDoc availability, OpenAPI JSON schema validation, CORS headers, error normalization, and dependency injection overrides.

---

## [1.2.0] - 2026-10-27

### Added
- **Retrieval V2 Explainability & Trust Engine (`src/retrieval_v2.py`):**
  - **Calibrated Confidence Scoring**: Implemented `compute_retrieval_confidence` combining logistic sigmoid normalized cross-encoder logits ($P_{\text{rerank}} = \sigma(s_{\text{rerank}})$, 70% weight) and bounded dense cosine similarity ($P_{\text{sim}}$, 30% weight) into High ($\ge 70\%$), Medium ($40\% - 70\%$), and Low ($< 40\%$) tiers.
  - **Automated Explainability**: Generates human-readable mathematical explanations breaking down component contributions and factual grounding strength.
  - **Chunk Highlighting & Citation Attribution**: Implemented `identify_used_chunks` detecting explicit citations (`[Source N]`, `Source N`) and fallback lexical overlaps, with `highlight_chunk_html` wrapping matching evidence in `<mark class="docmind-highlight">` while strictly preserving 100% of original formatting, newlines, and whitespace.
  - **Metadata Filtering Engine**: Implemented `matches_metadata_filter` and `filter_chunks_by_metadata` supporting filtering by filename, document type, exact upload date, and date ranges.
  - **Telemetry Tracking**: Implemented `RetrievalMetrics` capturing retrieval, reranking, generation, and total wall-clock latencies alongside candidate volume counts.
  - **Recent Queries Session History**: Implemented `add_recent_query` managing a 10-query deduplicated LRU cache.
- **HybridRetriever Integration (`src/retriever.py`):**
  - Added optional `metadata_filter` parameter to `HybridRetriever.retrieve()`, filtering candidate pools before RRF fusion with zero changes to RRF mathematics ($k=60$).
  - Attached `similarity_score` to retrieved chunk dictionaries for downstream explainability.
- **Streamlit Retrieval V2 Interface (`app.py`):**
  - **Enhanced Source Cards**: Displays filename, page number, chunk number, dense similarity score, and cross-encoder reranker score for every candidate.
  - **Grounded Source Highlighting**: Visually differentiates primary grounding sources (`🎯 Primary Source Used for Answer Generation`) with glow borders and formatted highlighted spans.
  - **Retrieval Confidence Banner**: Displays confidence level, percentage, color badge, and formula breakdown above history results.
  - **Telemetry Metrics Panel**: Displays Retrieval Latency, Reranking Latency, Generation Latency, Total Response Time, and candidate count metrics.
  - **Interactive Metadata Filters**: Dropdown filters for document, document type, and upload date.
  - **Recent Query Chips**: Clickable buttons for single-click re-execution of recent queries.
- **Retrieval V2 Documentation (`RETRIEVAL_V2.md`):**
  - Created architectural guide detailing confidence formulas, pipeline flow, metadata filtering, latency telemetry, and UI changes.
- **Automated Unit Tests (`tests/test_retrieval_v2.py`):**
  - Added 21 unit tests covering confidence computation, metadata filters, formatting-preserving highlighting, telemetry, and recent queries.

---

## [1.1.0] - 2026-10-27

### Added
- **Ingestion Pipeline V2 Architecture (`src/ingestion.py`):**
  - Added support for DOCX (`.docx`) with dual-engine parser (optional `python-docx` + standard-library `zipfile` and `xml.etree.ElementTree` OpenXML fallback for zero external dependency execution).
  - Added support for Markdown (`.md`) ingestion preserving markdown formatting.
  - Added `load_documents(paths)` for batch ingestion of multiple files in a single operation.
  - Created structured data contracts: `DocumentMetadata` and `Document` dataclasses with `.to_dict()` serialization.
  - Extracted comprehensive document metadata: `filename`, `file_type`, `upload_timestamp` (ISO 8601 UTC), `page_count` (with legacy `pages` alias), `file_size` (bytes), and `source` path.
- **Granular Deletion & Dynamic Index Rebuilding (`src/vectorstore.py`):**
  - Added `delete_by_filename(filename)` performing instant NumPy array boolean row-slicing without re-embedding remaining documents.
  - Added `delete_by_metadata(key, value)` for metadata-driven pruning.
  - Added getter utilities: `get_documents()`, `get_metadata()`, and `get_all_filenames()`.
  - Enables instant BM25 index refit on remaining chunks in < 2ms without re-embedding other files.
- **Streamlit Ingestion V2 UI (`app.py`):**
  - Multi-file uploader (`accept_multiple_files=True`, `type=["pdf", "docx", "txt", "md"]`).
  - Stage-by-stage indexing progress bar with status messages.
  - Sidebar document management card list with format icons, file size, page count, chunk count, and per-document delete (`🗑️`) button.
  - Main area "Ingested Knowledge Base" expandable overview table showing complete metadata.
- **Ingestion V2 Architecture Guide (`INGESTION_V2.md`):**
  - Authored comprehensive guide detailing architecture, loaders, metadata schemas, dynamic index deletion mechanics, and backward compatibility.
- **Comprehensive Test Suite:**
  - Added DOCX unit tests (`test_load_docx_basic`, `test_load_docx_corrupted`, `test_load_docx_empty`, `test_load_docx_missing_file_raises`, `test_load_document_dispatch_docx`).
  - Added multi-file batch test (`test_load_documents_multiple`).
  - Added metadata schema test (`test_metadata_schema_fields`).
  - Added VectorStore deletion tests in `tests/test_vectorstore.py`.

### Changed
- **Unsupported File Extension Test (`tests/test_ingestion.py`):**
  - Updated fixture extension from `.docx` to `.xyz` to reflect official support for Word documents.
- **Markdown File Type Metadata:**
  - Ingestion V2 returns `file_type="md"` for `.md` files in accordance with the format taxonomy.

---

## [1.0.0] - 2026-10-27

### Added
- **Centralized Logging Architecture (`src/logger.py`):**
  - Created centralized logger configuration utility (`configure_logging` and `get_logger`).
  - Supports configurable log formats (`%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s`).
  - Added environment variable support via `DOCMIND_LOG_LEVEL` (defaults to `INFO`).
  - Configured stream handlers with thread safety and duplicate-handler suppression.
- **DocMind AI Package Metadata (`src/__init__.py`):**
  - Added package-level docstring and `__version__ = "1.0.0"`.
- **Object Representations (`__repr__`):**
  - Added formatted string representations to `RecursiveTextChunker` and integrated standard reprs across domain classes.

### Changed
- **Branding Renaming to "DocMind AI":**
  - Renamed user-facing titles, browser page titles, headers, badges, and captions across `app.py`, `README.md`, and all `src/` modules from "RAG Pipeline Demo" and "RAG From Scratch" to "DocMind AI".
  - Updated page icon to 🧠 and refreshed hero banner copy.
- **Logging Integration Across Core Modules:**
  - Integrated `src.logger.get_logger` into `src/utils.py`, `src/ingestion.py`, `src/chunker.py`, `src/embeddings.py`, `src/bm25.py`, `src/vectorstore.py`, `src/reranker.py`, `src/retriever.py`, `src/generator.py`, `src/evaluation.py`, and `app.py`.
- **Runtime API Key Detection (`app.py`):**
  - Replaced hardcoded `False` (`⏳ Pending`) status indicator in the UI pipeline step strip with dynamic detection (`has_api_key = bool(api_key.strip())`).
  - Status card now reactively indicates `✅ Ready` when an API key is provided and `⏳ Pending` when empty.
- **Type Annotations & Modern Typing:**
  - Standardized modern typing (`int | str` instead of `Union[int, str]`, `dict[str, Any]`, `list[dict[str, Any]]`) across all modules.
  - Enhanced type hints for function arguments and return types across all public APIs.
- **Docstrings & Educational Comments:**
  - Refined module and method docstrings across the entire `src/` directory to reflect the DocMind AI architecture while preserving all algorithmic explanations.

### Fixed
- **Cross-Platform Path Support in `source_basename` (`src/utils.py`):**
  - Fixed `source_basename()` to normalize Windows backslashes (`\`) into forward slashes (`/`) before extracting `Path.name`.
  - Resolves test failure in `tests/test_utils.py:test_source_basename_windows_path` on non-Windows (macOS/Linux) environments.
- **HTTP Error Propagation Contract in `LLMGenerator` (`src/generator.py`):**
  - Replaced ad-hoc `if not response.ok: raise RuntimeError(...)` with standard `response.raise_for_status()`.
  - Restored compatibility with `tests/test_generator.py:test_http_error_propagates` which expects `requests.exceptions.HTTPError`.
  - Removed hardcoded vendor error coupling ("Groq API Error").
- **PDF Ingestion Error Precedence (`src/ingestion.py`):**
  - Moved `resolve_path(path)` ahead of `import PyPDF2` in `load_pdf()`.
  - Ensures non-existent file paths correctly raise `FileNotFoundError` as specified in tests, rather than premature `ImportError`.

### Removed
- **Debug Print Statements (`src/generator.py`):**
  - Removed raw `print()` statements from `_call_api()` (`URL`, `MODEL`, `STATUS`, `RESPONSE`), eliminating stdout pollution and private payload leakage.
- **Duplicate Library Imports (`app.py`):**
  - Removed redundant `import pandas as pd` inside `tab_sources` block (already imported globally at line 16).
- **Dead & Unreachable Placeholders (`app.py`):**
  - Eliminated the un-updated placeholder logic for pipeline step 4 in `app.py`.

### Security
- **Information Leak Prevention:**
  - Removed unfiltered stdout logging of remote LLM responses, headers, and prompt data in `LLMGenerator`, preventing leakage of sensitive document contents to console and container log aggregators.

# DocMind AI — Backend Upload & Storage Architecture (Sprint 4.2)

## 1. Executive Summary

This specification defines the architectural design, data models, and service execution flows implemented in **Sprint 4.2** of the **DocMind AI Backend**.

The primary objective of Sprint 4.2 is to bridge the FastAPI backend infrastructure to the existing core AI engine ([`src/`](file:///Users/krishgupta/Downloads/Rag_From_Scratch-main/src)) while strictly honoring the following non-negotiable architectural constraints:
1. **Zero Modifications to AI Engine**: All retrieval, chunking, embedding, reranking, and generation algorithms in [`src/`](file:///Users/krishgupta/Downloads/Rag_From_Scratch-main/src) remain 100% mathematically and structurally unchanged.
2. **Hybrid Storage Segregation**:
   - **SQLite (via SQLAlchemy)**: Manages relational and tabular metadata (`documents` and `chat_history`).
   - **NumPy/JSON VectorStore**: Retains dense float32 vector matrices and chunk text mappings for microsecond-latency cosine similarity dot products.
3. **Decoupled Service Layer**: Encapsulates business logic in `UploadService` and `DocumentService`, accessible through FastAPI Dependency Injection (`deps.py`).

---

## 2. Hybrid Storage Segregation Rationale

```
+---------------------------------------------------------------------------------+
|                               DOCMIND AI STORAGE                                |
+---------------------------------------+-----------------------------------------+
|        SQLITE (Relational / ACID)     |       VECTORSTORE (Dense Indices)       |
+---------------------------------------+-----------------------------------------+
| Tables:                               | Files:                                  |
|   - documents (catalog & metadata)    |   - vector_store.npz (float32 matrix)   |
|   - chat_history (session turns)      |   - vector_store.json (chunk text & map)|
| Purpose:                              | Purpose:                                |
|   - Cataloging, audit logs            |   - Exact cosine similarity search      |
|   - Pagination, deletion lookups      |   - High-throughput dot-product math    |
|   - Zero BLOB/Vector storage overhead |   - In-memory NumPy cache               |
+---------------------------------------+-----------------------------------------+
```

### Architectural Justification
- **Relational Overhead Avoidance**: Storing large multidimensional embedding arrays (384-dim float32 vectors) inside SQLite BLOB or JSON columns creates severe I/O bottlenecks and serialization penalties during vector similarity searches.
- **Preserved Mathematical Equivalence**: By keeping the embeddings in [`src.vectorstore.VectorStore`](file:///Users/krishgupta/Downloads/Rag_From_Scratch-main/src/vectorstore.py), the hybrid retriever's dense cosine similarity search ($s_{\text{sim}} = \mathbf{e}_{\text{chunk}} \cdot \mathbf{e}_{\text{query}}$) remains bit-for-bit identical to the Streamlit UI and CLI pipelines.

---

## 3. SQLite Database Schema Specification

The database is initialized by default at `data/docmind.db` using SQLAlchemy 2.0 declarative models (`backend/app/db/models/`).

### A. `documents` Table
Stores high-level catalog metadata for every ingested document.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | Primary Key, Indexed | Unique UUID identifier for the document record |
| `filename` | `VARCHAR(255)` | Not Null, Indexed | Original sanitized filename (e.g. `annual_report.pdf`) |
| `file_type` | `VARCHAR(32)` | Not Null | File format extension (`pdf`, `docx`, `txt`, `md`) |
| `file_size` | `INTEGER` | Not Null | File size in bytes |
| `page_count` | `INTEGER` | Nullable | Extracted page count (for PDF / DOCX) |
| `chunk_count`| `INTEGER` | Not Null, Default `0` | Number of text chunks generated and stored in VectorStore |
| `upload_timestamp` | `DATETIME` | Not Null, UTC | ISO 8601 UTC timestamp of ingestion completion |
| `file_path` | `VARCHAR(1024)` | Not Null | Filesystem path on server (`data/uploads/<filename>`) |
| `status` | `VARCHAR(32)` | Not Null, Default `'indexed'` | Processing status (`indexed`, `processing`, `error`) |

### B. `chat_history` Table
Stores conversational interactions, user queries, answers, and retrieval metrics.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | Primary Key, Indexed | Unique UUID identifier for the chat turn |
| `session_id` | `VARCHAR(64)` | Not Null, Indexed | Session identifier for multi-turn conversation threads |
| `query` | `TEXT` | Not Null | Raw query string entered by the user |
| `answer` | `TEXT` | Not Null | LLM-generated answer grounded in retrieved chunks |
| `retrieved_sources` | `TEXT` | Nullable | JSON-serialized array of source citations and chunk scores |
| `confidence_score` | `FLOAT` | Nullable | Calibrated confidence score (0.0 to 1.0) |
| `latency_ms` | `FLOAT` | Nullable | Total wall-clock query-to-answer latency in ms |
| `created_at` | `DATETIME` | Not Null, UTC | UTC timestamp of the interaction |

---

## 4. Component Architecture & Layering

```mermaid
flowchart TD
    subgraph ClientLayer ["Client / Consumer Layer"]
        HTTPClient["HTTP Client (Browser / React / cURL)"]
    end

    subgraph APILayer ["FastAPI Routing Layer (backend/app/api/v1/endpoints)"]
        UploadEP["POST /api/v1/upload<br/>(upload.py)"]
        ListEP["GET /api/v1/documents<br/>(documents.py)"]
        GetEP["GET /api/v1/documents/{id}<br/>(documents.py)"]
        DeleteEP["DELETE /api/v1/documents/{id}<br/>(documents.py)"]
    end

    subgraph ServiceLayer ["Service Layer (backend/app/services)"]
        UploadSvc["UploadService<br/>(upload_service.py)"]
        DocSvc["DocumentService<br/>(document_service.py)"]
    end

    subgraph DBLayer ["Database Layer (backend/app/db)"]
        SQLAlchemyEngine["SQLAlchemy Engine & SessionLocal<br/>(session.py)"]
        DocModel["DocumentModel<br/>(models/document.py)"]
        ChatModel["ChatHistoryModel<br/>(models/chat.py)"]
    end

    subgraph AIEngine ["Untouched AI Core Engine (src/)"]
        IngestionMod["src.ingestion.load_document<br/>(Multi-format loaders: PDF, DOCX, TXT, MD)"]
        ChunkerMod["src.chunker.RecursiveTextChunker<br/>(chunk_size=512, overlap=64)"]
        EmbeddingMod["src.embeddings.EmbeddingModel<br/>(all-MiniLM-L6-v2)"]
        VectorStoreMod["src.vectorstore.VectorStore<br/>(Exact cosine similarity)"]
    end

    subgraph StorageLayer ["Filesystem Storage"]
        UploadDisk["data/uploads/<filename><br/>(Raw uploaded files)"]
        StoreDisk["data/store/vector_store.npz & .json<br/>(NumPy matrices & chunk metadata)"]
        SQLiteDB["data/docmind.db<br/>(SQLite database file)"]
    end

    HTTPClient -->|Multipart File| UploadEP
    HTTPClient -->|Query Params| ListEP
    HTTPClient -->|Document UUID| GetEP
    HTTPClient -->|Document UUID| DeleteEP

    UploadEP -->|process_upload| UploadSvc
    ListEP -->|list_documents| DocSvc
    GetEP -->|get_document_by_id| DocSvc
    DeleteEP -->|delete_document| DocSvc

    UploadSvc -->|Save File| UploadDisk
    UploadSvc -->|Parse Text| IngestionMod
    UploadSvc -->|Split Text| ChunkerMod
    UploadSvc -->|Generate Embeddings| EmbeddingMod
    UploadSvc -->|Update & Save| VectorStoreMod
    VectorStoreMod -->|Persist .npz & .json| StoreDisk
    UploadSvc -->|Insert / Update Record| DocModel

    DocSvc -->|Query Records| DocModel
    DocSvc -->|Delete Record| DocModel
    DocSvc -->|delete_by_filename| VectorStoreMod
    DocSvc -->|Unlink File| UploadDisk

    DocModel --> SQLAlchemyEngine
    ChatModel --> SQLAlchemyEngine
    SQLAlchemyEngine --> SQLiteDB
```

---

## 5. End-to-End Execution Workflows

### A. Document Upload & Ingestion Flow (`POST /api/v1/upload`)

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client / Frontend
    participant Endpoint as POST /api/v1/upload
    participant Service as UploadService
    participant Disk as data/uploads/
    participant Ingestion as src.ingestion.load_document
    participant Chunker as src.chunker.RecursiveTextChunker
    participant Embedder as src.embeddings.EmbeddingModel
    participant Store as src.vectorstore.VectorStore
    participant DB as SQLite (DocumentModel)

    Client->>Endpoint: POST /api/v1/upload (multipart/form-data)
    Endpoint->>Service: process_upload(file, db)
    
    Service->>Service: Validate filename, extension (.pdf, .docx, .txt, .md), and size
    alt Validation Failure
        Service-->>Endpoint: Raise ValidationException (422)
        Endpoint-->>Client: 422 Unprocessable Content (Standard Error Envelope)
    end

    Service->>Disk: Write content to data/uploads/<filename>
    Service->>Ingestion: load_document(target_path)
    Ingestion-->>Service: doc {text, filename, metadata}

    Service->>Chunker: split_text(doc.text)
    Chunker-->>Service: chunks [{text, chunk_index}, ...]

    Service->>Embedder: embed_texts(chunk_texts)
    Embedder-->>Service: embeddings (N, 384) float32 matrix

    Service->>Store: delete_by_filename(filename) [Purge any prior version]
    Service->>Store: add(embeddings, chunk_texts, chunk_metas)
    Service->>Store: save(data/store/vector_store)

    Service->>DB: Query existing DocumentModel by filename
    alt File Already Exists
        Service->>DB: Update existing record (file_size, chunk_count, timestamp)
    else New File
        Service->>DB: Insert new DocumentModel (UUID, metadata)
    end
    DB-->>Service: db_doc record committed

    Service-->>Endpoint: Return DocumentModel
    Endpoint-->>Client: 201 Created (BaseResponse[UploadResponseData])
```

---

### B. Document Deletion & Synchronization Flow (`DELETE /api/v1/documents/{id}`)

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client / Frontend
    participant Endpoint as DELETE /api/v1/documents/{id}
    participant Service as DocumentService
    participant DB as SQLite (DocumentModel)
    participant Store as src.vectorstore.VectorStore
    participant Disk as data/uploads/

    Client->>Endpoint: DELETE /api/v1/documents/{doc_id}
    Endpoint->>Service: delete_document(db, doc_id, vector_store, store_path)

    Service->>DB: select DocumentModel by id
    alt Document Not Found
        Service-->>Endpoint: Raise ResourceNotFoundException (404)
        Endpoint-->>Client: 404 Not Found (Standard Error Envelope)
    end

    Service->>DB: db.delete(doc) & db.commit()
    Service->>Store: delete_by_filename(doc.filename)
    Store-->>Service: removed_chunks count
    Service->>Store: save(store_path) [Re-persist updated NumPy & JSON files]

    Service->>Disk: os.remove(doc.file_path) [Delete uploaded file]

    Service-->>Endpoint: Return {id, filename, removed_chunks}
    Endpoint-->>Client: 200 OK (BaseResponse[DocumentDeleteData])
```

---

## 6. Error Handling & Validation Matrix

All API endpoints trap domain exceptions into a uniform JSON response envelope:

| Failure Mode | Detection Point | HTTP Code | Error Type | Returned Detail |
| :--- | :--- | :--- | :--- | :--- |
| **Unsupported Extension** | `UploadService` | `422` | `validation_error` | Lists attempted extension and allowed formats |
| **Empty File (0 bytes)** | `UploadService` | `422` | `validation_error` | Indicates file contains 0 bytes |
| **Oversized File (> 50MB)**| `UploadService` | `422` | `validation_error` | Reports size vs `MAX_UPLOAD_SIZE_BYTES` |
| **Non-Existent Document** | `DocumentService` | `404` | `resource_not_found` | Reports missing document UUID |
| **Ingestion Parse Failure**| `load_document` | `422` | `validation_error` | Reports format parsing error details |
| **Unhandled Server Error** | Global Exception Handler | `500` | `internal_server_error` | Logs server traceback; sanitizes response |

---

## 7. Integration Test Verification

The upload and document management foundation is backed by 11 integration tests in [`tests/test_backend_upload.py`](file:///Users/krishgupta/Downloads/Rag_From_Scratch-main/tests/test_backend_upload.py):

1. **`test_upload_txt_file_success`**: Validates uploading plain text files, chunk generation, VectorStore updates, and SQLite persistence.
2. **`test_upload_markdown_file_success`**: Validates markdown file structure retention and indexing.
3. **`test_upload_unsupported_extension_fails`**: Validates rejection of unauthorized file types (`.exe`).
4. **`test_upload_empty_file_fails`**: Validates rejection of 0-byte file uploads.
5. **`test_list_documents`**: Validates pagination and metadata listing from SQLite.
6. **`test_get_document_by_id`**: Validates single document record retrieval by UUID.
7. **`test_get_document_by_id_not_found`**: Validates 404 on non-existent document ID.
8. **`test_delete_document_success`**: Validates atomic removal from SQLite, VectorStore chunk purging, and disk file deletion.
9. **`test_delete_document_not_found`**: Validates 404 on deleting a non-existent document.
10. **`test_chat_history_table_model`**: Validates `chat_history` table persistence and column types.
11. **`test_reupload_same_filename_replaces`**: Validates idempotency and in-place vector index replacement upon uploading identical filenames.

---

## 8. Mathematical & Algorithmic Invariance Summary

No algorithms in [`src/`](file:///Users/krishgupta/Downloads/Rag_From_Scratch-main/src) were modified:
- **`RecursiveTextChunker`**: Tokenization boundaries and overlap mechanics remain identical.
- **`EmbeddingModel`**: Bi-encoder mean pooling and L2 normalization formulas remain identical.
- **`VectorStore`**: Dense cosine similarity via NumPy matrix multiplication ($\mathbf{A} \cdot \mathbf{b}$) remains identical.
- **`BM25` & `HybridRetriever`**: Reciprocal Rank Fusion ($k=60$) remains identical.

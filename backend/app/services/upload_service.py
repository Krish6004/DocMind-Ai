"""
UploadService for validating, saving, and ingesting documents into DocMind AI.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.errors import ValidationException
from backend.app.core.logging import get_logger
from backend.app.db.models.document import DocumentModel
from src.chunker import RecursiveTextChunker
from src.ingestion import load_document
from src.vectorstore import VectorStore

logger = get_logger(__name__)


class UploadService:
    """
    Coordinates end-to-end document upload processing:
      1. Validates file format, size, and filename.
      2. Saves the uploaded file to data/uploads/.
      3. Invokes the existing ingestion pipeline (src.ingestion).
      4. Invokes the existing chunker (src.chunker.RecursiveTextChunker).
      5. Invokes the existing embedding pipeline (src.embeddings.EmbeddingModel).
      6. Updates and saves the NumPy/JSON VectorStore.
      7. Persists document metadata into SQLite.
    """

    def __init__(
        self,
        settings: Settings,
        vector_store: VectorStore,
        embedding_model: Any,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> None:
        self.settings = settings
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.chunker = RecursiveTextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    async def process_upload(
        self,
        file: UploadFile,
        db: Session,
        user_id: str = "default",
    ) -> DocumentModel:
        """
        Execute full upload, ingestion, chunking, embedding, vector store update,
        and SQLite metadata persistence.

        Args:
            file: FastAPI UploadFile from request.
            db: Active database session.

        Returns:
            Created/updated DocumentModel record.

        Raises:
            ValidationException: If validation fails.
        """
        # 1. Validate filename
        raw_filename = file.filename or ""
        sanitized_filename = Path(raw_filename).name.strip()
        if not sanitized_filename:
            raise ValidationException("Uploaded file must have a non-empty filename.")

        # 2. Validate file extension
        suffix = Path(sanitized_filename).suffix.lower()
        if suffix not in self.settings.ALLOWED_EXTENSIONS:
            allowed = sorted(list(self.settings.ALLOWED_EXTENSIONS))
            raise ValidationException(
                f"Unsupported file type '{suffix}'. Allowed formats: {', '.join(allowed)}",
                details={"filename": sanitized_filename, "extension": suffix, "allowed": allowed},
            )

        # 3. Read content & validate file size
        content = await file.read()
        file_size = len(content)
        if file_size == 0:
            raise ValidationException(
                f"File '{sanitized_filename}' is empty (0 bytes).",
                details={"filename": sanitized_filename, "file_size": 0},
            )

        if file_size > self.settings.MAX_UPLOAD_SIZE_BYTES:
            raise ValidationException(
                f"File '{sanitized_filename}' exceeds maximum allowed size of {self.settings.MAX_UPLOAD_SIZE_BYTES} bytes.",
                details={"filename": sanitized_filename, "file_size": file_size, "max_size": self.settings.MAX_UPLOAD_SIZE_BYTES},
            )

        # 4. Save to data/uploads (user-scoped directory when authenticated)
        upload_dir = self.settings.UPLOAD_DIR / user_id if user_id and user_id != "default" else self.settings.UPLOAD_DIR
        upload_dir.mkdir(parents=True, exist_ok=True)
        target_path = upload_dir / sanitized_filename

        try:
            with open(target_path, "wb") as f:
                f.write(content)
            logger.info("Saved uploaded file '%s' to '%s' (%d bytes)", sanitized_filename, target_path, file_size)
        except OSError as exc:
            logger.exception("Failed to write uploaded file to disk: %s", exc)
            raise ValidationException(f"Failed to save file to server storage: {exc}") from exc

        # 5. Call existing ingestion pipeline (offloaded to threadpool)
        try:
            doc = await asyncio.to_thread(load_document, str(target_path))
            doc_text = doc.get("text", "")
            doc_metadata = doc.get("metadata", {})
        except Exception as exc:
            logger.exception("Ingestion failed for '%s': %s", sanitized_filename, exc)
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            raise ValidationException(
                f"Failed to parse and extract text from '{sanitized_filename}': {exc}",
                details={"filename": sanitized_filename, "error": str(exc)},
            ) from exc

        # 6. Call existing chunker (offloaded to threadpool)
        chunks = await asyncio.to_thread(self.chunker.split_text, doc_text)
        chunk_count = len(chunks)
        logger.info("Generated %d chunks for document '%s'", chunk_count, sanitized_filename)

        # 7. Call existing embedding pipeline & update vector store
        if chunk_count > 0:
            chunk_texts = [c["text"] for c in chunks]
            user_file_key = f"{user_id}:{sanitized_filename}"
            chunk_metas = [
                {
                    "source": str(target_path),
                    "filename": sanitized_filename,
                    "user_id": user_id,
                    "user_file_key": user_file_key,
                    "chunk_index": c["chunk_index"],
                    "file_type": doc_metadata.get("file_type", suffix.lstrip(".")),
                    "file_size": file_size,
                    "upload_timestamp": doc_metadata.get("upload_timestamp", datetime.now(timezone.utc).isoformat()),
                    "page_count": doc_metadata.get("page_count"),
                }
                for c in chunks
            ]

            embeddings = await asyncio.to_thread(self.embedding_model.embed_texts, chunk_texts, 32, False)

            # Synchronize VectorStore: Remove prior chunks for this user's file only
            if user_id and user_id != "default":
                self.vector_store.delete_by_metadata("user_file_key", user_file_key)
            else:
                self.vector_store.delete_by_filename(sanitized_filename)
            self.vector_store.add(embeddings, chunk_texts, chunk_metas)

            # Persist VectorStore state to data/store
            store_dir = self.settings.STORE_DIR
            store_dir.mkdir(parents=True, exist_ok=True)
            store_path = store_dir / "vector_store"
            try:
                await asyncio.to_thread(self.vector_store.save, str(store_path))
                logger.info("Persisted VectorStore (%d chunks) to '%s'", len(self.vector_store), store_path)
            except Exception as exc:
                logger.warning("Failed to persist VectorStore to disk: %s", exc)
        else:
            logger.warning("Document '%s' produced 0 chunks (empty content after parsing)", sanitized_filename)

        # 8. Save metadata to SQLite (scoped by user_id)
        existing_doc_stmt = select(DocumentModel).where(
            DocumentModel.filename == sanitized_filename,
            DocumentModel.user_id == user_id,
        )
        existing_doc = db.scalar(existing_doc_stmt)
        if existing_doc is not None:
            # Update existing document entry
            logger.info("Updating existing document metadata for '%s' (id='%s')", sanitized_filename, existing_doc.id)
            existing_doc.file_size = file_size
            existing_doc.file_type = suffix.lstrip(".") if suffix else doc_metadata.get("file_type", "txt")
            existing_doc.page_count = doc_metadata.get("page_count")
            existing_doc.chunk_count = chunk_count
            existing_doc.upload_timestamp = datetime.now(timezone.utc)
            existing_doc.file_path = str(target_path)
            existing_doc.status = "indexed"
            db.commit()
            db.refresh(existing_doc)
            return existing_doc
        else:
            # Create new document record
            new_doc = DocumentModel(
                id=uuid.uuid4().hex,
                user_id=user_id,
                filename=sanitized_filename,
                file_type=suffix.lstrip(".") if suffix else doc_metadata.get("file_type", "txt"),
                file_size=file_size,
                page_count=doc_metadata.get("page_count"),
                chunk_count=chunk_count,
                upload_timestamp=datetime.now(timezone.utc),
                file_path=str(target_path),
                status="indexed",
            )
            db.add(new_doc)
            db.commit()
            db.refresh(new_doc)
            logger.info("Persisted new document record in SQLite: %r", new_doc)
            return new_doc

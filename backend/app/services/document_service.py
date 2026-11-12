"""
DocumentService for managing document metadata and lifecycle in DocMind AI.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.errors import ResourceNotFoundException
from backend.app.core.logging import get_logger
from backend.app.db.models.document import DocumentModel
from src.vectorstore import VectorStore

logger = get_logger(__name__)


class DocumentService:
    """
    Coordinates document metadata queries in SQLite and synchronization
    with physical disk files and VectorStore indices.
    """

    def list_documents(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DocumentModel]:
        """
        List all indexed documents ordered by upload timestamp descending.
        """
        stmt = (
            select(DocumentModel)
            .order_by(DocumentModel.upload_timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def get_document_count(self, db: Session) -> int:
        """
        Return the total number of documents recorded in SQLite.
        """
        from sqlalchemy import func
        stmt = select(func.count(DocumentModel.id))
        count = db.scalar(stmt)
        return count or 0

    def get_document_by_id(self, db: Session, doc_id: str) -> DocumentModel | None:
        """
        Fetch a document record by its UUID.
        """
        stmt = select(DocumentModel).where(DocumentModel.id == doc_id)
        return db.scalar(stmt)

    def get_document_by_filename(self, db: Session, filename: str) -> DocumentModel | None:
        """
        Fetch a document record by its sanitized filename.
        """
        stmt = select(DocumentModel).where(DocumentModel.filename == filename)
        return db.scalar(stmt)

    def delete_document(
        self,
        db: Session,
        doc_id: str,
        vector_store: VectorStore,
        store_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Delete a document:
          1. Removes metadata from SQLite.
          2. Invokes existing delete_by_filename() in the NumPy/JSON VectorStore.
          3. Deletes the uploaded physical file from disk.
          4. Persists updated VectorStore state to disk if store_path is provided.

        Args:
            db: Active database session.
            doc_id: UUID of the document to delete.
            vector_store: In-memory / singleton VectorStore instance.
            store_path: Path to persist the updated VectorStore state.

        Returns:
            Dict containing id, filename, and count of removed vector chunks.

        Raises:
            ResourceNotFoundException: If the document is not found.
        """
        doc = self.get_document_by_id(db, doc_id)
        if doc is None:
            raise ResourceNotFoundException(
                message=f"Document with ID '{doc_id}' not found.",
                details={"doc_id": doc_id},
            )

        filename = doc.filename
        file_path = doc.file_path

        # 1. Remove metadata from SQLite
        logger.info("Removing metadata from SQLite for document id='%s' (filename='%s')", doc_id, filename)
        db.delete(doc)
        db.commit()

        # 2. Invoke existing delete_by_filename in VectorStore
        removed_chunks = vector_store.delete_by_filename(filename)
        logger.info("Removed %d chunks for '%s' from VectorStore", removed_chunks, filename)

        # 3. Persist updated VectorStore to disk
        if store_path is not None:
            try:
                vector_store.save(str(store_path))
                logger.info("Persisted updated VectorStore to '%s'", store_path)
            except Exception as e:
                logger.warning("Failed to save VectorStore after deletion: %s", e)

        # 4. Delete the uploaded file from disk
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info("Deleted physical file from disk: %s", file_path)
            except OSError as exc:
                logger.warning("Failed to delete physical file '%s': %s", file_path, exc)

        return {
            "id": doc_id,
            "filename": filename,
            "removed_chunks": removed_chunks,
        }

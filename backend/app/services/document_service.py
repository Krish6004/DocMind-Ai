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
        user_id: str = "default",
    ) -> list[DocumentModel]:
        """
        List indexed documents for the specified user ordered by upload timestamp descending.
        """
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.user_id == user_id)
            .order_by(DocumentModel.upload_timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def get_document_count(self, db: Session, user_id: str = "default") -> int:
        """
        Return the total number of documents recorded in SQLite for the user.
        """
        from sqlalchemy import func
        stmt = select(func.count(DocumentModel.id)).where(DocumentModel.user_id == user_id)
        count = db.scalar(stmt)
        return count or 0

    def get_document_by_id(self, db: Session, doc_id: str, user_id: str = "default") -> DocumentModel | None:
        """
        Fetch a document record by its UUID scoped to user_id.
        """
        stmt = select(DocumentModel).where(
            DocumentModel.id == doc_id,
            DocumentModel.user_id == user_id,
        )
        return db.scalar(stmt)

    def get_document_by_filename(self, db: Session, filename: str, user_id: str = "default") -> DocumentModel | None:
        """
        Fetch a document record by its sanitized filename scoped to user_id.
        """
        stmt = select(DocumentModel).where(
            DocumentModel.filename == filename,
            DocumentModel.user_id == user_id,
        )
        return db.scalar(stmt)

    def delete_document(
        self,
        db: Session,
        doc_id: str,
        vector_store: VectorStore,
        store_path: str | Path | None = None,
        user_id: str = "default",
    ) -> dict[str, Any]:
        """
        Delete a user-owned document from SQLite, VectorStore, and disk.
        """
        doc = self.get_document_by_id(db, doc_id, user_id=user_id)
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

        # 2. Remove only this user's chunks from VectorStore
        if user_id and user_id != "default":
            removed_chunks = vector_store.delete_by_metadata("user_file_key", f"{user_id}:{filename}")
        else:
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

"""
SQLAlchemy ORM model for document metadata.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from backend.app.db.base import Base


class DocumentModel(Base):
    """
    SQLAlchemy model representing stored document metadata in SQLite.

    Strict Rule: Only metadata is stored here. Embeddings and chunk vectors
    are maintained in the NumPy/JSON VectorStore.
    """

    __tablename__ = "documents"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: uuid.uuid4().hex,
        index=True,
        doc="Unique UUID identifier for the document record",
    )
    filename = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Original sanitized filename",
    )
    file_type = Column(
        String(32),
        nullable=False,
        doc="File extension / format (pdf, docx, txt, md)",
    )
    file_size = Column(
        Integer,
        nullable=False,
        doc="File size in bytes",
    )
    page_count = Column(
        Integer,
        nullable=True,
        doc="Extracted page count (if applicable)",
    )
    chunk_count = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Total text chunks generated and indexed in VectorStore",
    )
    upload_timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="UTC timestamp when the file was uploaded and indexed",
    )
    file_path = Column(
        String(1024),
        nullable=False,
        doc="Filesystem path where the raw uploaded file is stored",
    )
    status = Column(
        String(32),
        nullable=False,
        default="indexed",
        doc="Document processing status (e.g. indexed, processing, error)",
    )

    def to_dict(self) -> dict:
        """Convert ORM model to dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "page_count": self.page_count,
            "chunk_count": self.chunk_count,
            "upload_timestamp": (
                self.upload_timestamp.isoformat()
                if self.upload_timestamp
                else None
            ),
            "file_path": self.file_path,
            "status": self.status,
        }

    def __repr__(self) -> str:
        return f"<DocumentModel(id='{self.id}', filename='{self.filename}', chunks={self.chunk_count})>"

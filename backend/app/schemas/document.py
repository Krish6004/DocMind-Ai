"""
Pydantic schemas for document ingestion and management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    """Base fields for a document record."""

    filename: str = Field(..., description="Sanitized original document filename")
    file_type: str = Field(..., description="Document file extension/format (e.g. pdf, docx, txt, md)")
    file_size: int = Field(..., description="File size in bytes")
    page_count: int | None = Field(default=None, description="Total pages if applicable")
    chunk_count: int = Field(default=0, description="Number of text chunks indexed")
    status: str = Field(default="indexed", description="Processing status")


class DocumentOut(DocumentBase):
    """Schema returned when retrieving a document record."""

    id: str = Field(..., description="Unique UUID identifier for the document")
    upload_timestamp: datetime = Field(..., description="UTC timestamp when document was uploaded")
    file_path: str | None = Field(default=None, description="Path where file is stored on server")

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Schema returned when listing all documents."""

    total: int = Field(..., description="Total number of indexed documents in the database")
    documents: list[DocumentOut] = Field(..., description="List of document metadata items")


class UploadResponseData(DocumentBase):
    """Data payload returned on successful file upload."""

    id: str = Field(..., description="Assigned UUID for the newly indexed document")
    upload_timestamp: datetime = Field(..., description="UTC timestamp of completion")
    message: str = Field(default="Document uploaded and indexed successfully", description="Status message")

    model_config = ConfigDict(from_attributes=True)


class DocumentDeleteData(BaseModel):
    """Data payload returned when deleting a document."""

    id: str = Field(..., description="UUID of the deleted document")
    filename: str = Field(..., description="Filename of the deleted document")
    removed_chunks: int = Field(..., description="Number of chunks removed from VectorStore")
    message: str = Field(default="Document and associated vector chunks removed successfully", description="Status message")

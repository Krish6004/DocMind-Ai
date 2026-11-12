"""
Document management endpoints for DocMind AI.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_app_settings,
    get_database_session,
    get_document_service,
    get_vector_store,
)
from backend.app.core.config import Settings
from backend.app.core.errors import ResourceNotFoundException
from backend.app.schemas.common import BaseResponse
from backend.app.schemas.document import (
    DocumentDeleteData,
    DocumentListResponse,
    DocumentOut,
)
from backend.app.services.document_service import DocumentService
from src.vectorstore import VectorStore

router = APIRouter()


@router.get(
    "",
    response_model=BaseResponse[DocumentListResponse],
    status_code=status.HTTP_200_OK,
    summary="List Ingested Documents",
    description="Retrieve all indexed documents and their structured metadata from SQLite.",
)
def list_documents(
    skip: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=100, ge=1, le=500, description="Pagination limit"),
    db: Session = Depends(get_database_session),
    doc_service: DocumentService = Depends(get_document_service),
) -> BaseResponse[DocumentListResponse]:
    """
    List all documents tracked in the SQLite knowledge base.
    """
    docs = doc_service.list_documents(db=db, skip=skip, limit=limit)
    total = doc_service.get_document_count(db=db)

    doc_items = [
        DocumentOut(
            id=d.id,
            filename=d.filename,
            file_type=d.file_type,
            file_size=d.file_size,
            page_count=d.page_count,
            chunk_count=d.chunk_count,
            upload_timestamp=d.upload_timestamp,
            file_path=d.file_path,
            status=d.status,
        )
        for d in docs
    ]

    return BaseResponse(
        success=True,
        message=f"Retrieved {len(doc_items)} document(s).",
        data=DocumentListResponse(total=total, documents=doc_items),
    )


@router.get(
    "/{doc_id}",
    response_model=BaseResponse[DocumentOut],
    status_code=status.HTTP_200_OK,
    summary="Get Document by ID",
    description="Retrieve metadata for a specific document by its UUID.",
)
def get_document(
    doc_id: str,
    db: Session = Depends(get_database_session),
    doc_service: DocumentService = Depends(get_document_service),
) -> BaseResponse[DocumentOut]:
    """
    Get a single document's metadata.
    """
    doc = doc_service.get_document_by_id(db=db, doc_id=doc_id)
    if doc is None:
        raise ResourceNotFoundException(
            message=f"Document with ID '{doc_id}' not found.",
            details={"doc_id": doc_id},
        )

    return BaseResponse(
        success=True,
        message="Document metadata retrieved successfully.",
        data=DocumentOut(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            page_count=doc.page_count,
            chunk_count=doc.chunk_count,
            upload_timestamp=doc.upload_timestamp,
            file_path=doc.file_path,
            status=doc.status,
        ),
    )


@router.delete(
    "/{doc_id}",
    response_model=BaseResponse[DocumentDeleteData],
    status_code=status.HTTP_200_OK,
    summary="Delete Document",
    description=(
        "Delete a document by UUID. Removes metadata from SQLite, "
        "invokes delete_by_filename() in VectorStore, and deletes the uploaded file."
    ),
)
def delete_document(
    doc_id: str,
    db: Session = Depends(get_database_session),
    doc_service: DocumentService = Depends(get_document_service),
    vector_store: VectorStore = Depends(get_vector_store),
    settings: Settings = Depends(get_app_settings),
) -> BaseResponse[DocumentDeleteData]:
    """
    Delete a document from SQLite, VectorStore, and disk.
    """
    store_path = settings.STORE_DIR / "vector_store"
    result = doc_service.delete_document(
        db=db,
        doc_id=doc_id,
        vector_store=vector_store,
        store_path=store_path,
    )

    return BaseResponse(
        success=True,
        message=f"Successfully deleted document '{result['filename']}' ({result['removed_chunks']} chunks removed).",
        data=DocumentDeleteData(
            id=result["id"],
            filename=result["filename"],
            removed_chunks=result["removed_chunks"],
            message="Document record, vector chunks, and source file deleted.",
        ),
    )

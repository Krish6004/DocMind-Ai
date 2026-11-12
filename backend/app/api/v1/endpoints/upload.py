"""
Upload API endpoints for DocMind AI.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_database_session, get_upload_service
from backend.app.schemas.common import BaseResponse
from backend.app.schemas.document import UploadResponseData
from backend.app.services.upload_service import UploadService

router = APIRouter()


@router.post(
    "/upload",
    response_model=BaseResponse[UploadResponseData],
    status_code=status.HTTP_201_CREATED,
    summary="Upload & Index Document",
    description=(
        "Upload a document (.pdf, .docx, .txt, .md). The backend validates "
        "the file, extracts text, generates chunks, computes embeddings, "
        "updates the VectorStore, and records metadata in SQLite."
    ),
)
async def upload_document(
    file: UploadFile = File(..., description="The document file to upload and index"),
    db: Session = Depends(get_database_session),
    upload_service: UploadService = Depends(get_upload_service),
) -> BaseResponse[UploadResponseData]:
    """
    Handle document upload, chunking, embedding, and indexing.
    """
    doc_record = await upload_service.process_upload(file=file, db=db)

    payload = UploadResponseData(
        id=doc_record.id,
        filename=doc_record.filename,
        file_type=doc_record.file_type,
        file_size=doc_record.file_size,
        page_count=doc_record.page_count,
        chunk_count=doc_record.chunk_count,
        upload_timestamp=doc_record.upload_timestamp,
        status=doc_record.status,
        message=f"Document '{doc_record.filename}' indexed successfully ({doc_record.chunk_count} chunks).",
    )

    return BaseResponse(
        success=True,
        message="Document uploaded and indexed successfully.",
        data=payload,
    )

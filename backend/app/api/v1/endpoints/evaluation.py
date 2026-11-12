"""
Enterprise Evaluation & Benchmarking REST API Endpoints (Sprint 6.0).

Routes mounted under /api/v1/evaluation:
  - GET  /latest   : Most recent evaluated RAG turn
  - GET  /history  : Last 100 evaluation records
  - GET  /summary  : Aggregated dashboard scores, trends, provider comparison & heatmap
  - POST /run      : Execute automated 50+ query benchmark suite
  - GET  /export   : Export CSV, JSON, or PDF evaluation report
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_current_user_id,
    get_database_session,
    get_evaluation_service,
    get_provider_manager,
    get_reranker,
    get_retriever,
)
from backend.app.schemas.common import BaseResponse
from backend.app.schemas.evaluation import (
    BenchmarkRunRequest,
    BenchmarkRunResponse,
    EvaluationHistoryListResponse,
    EvaluationRecord,
    EvaluationSummaryResponse,
)
from backend.app.services.evaluation_service import EvaluationService

router = APIRouter()


@router.get(
    "/latest",
    response_model=BaseResponse[EvaluationRecord | None],
    status_code=status.HTTP_200_OK,
    summary="Get Latest Evaluation",
    description="Retrieve the most recent evaluation record stored in evaluation_history.",
)
def get_latest_evaluation(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database_session),
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
) -> BaseResponse[EvaluationRecord | None]:
    record = evaluation_service.get_latest(db, user_id=user_id)
    return BaseResponse(
        success=True,
        message="Retrieved latest evaluation record." if record else "No evaluations recorded yet.",
        data=record,
    )


@router.get(
    "/history",
    response_model=BaseResponse[EvaluationHistoryListResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Evaluation History",
    description="Retrieve up to the last 100 evaluation records in reverse chronological order.",
)
def get_evaluation_history(
    limit: int = Query(default=100, ge=1, le=500, description="Max evaluation records to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database_session),
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
) -> BaseResponse[EvaluationHistoryListResponse]:
    history = evaluation_service.get_history(db, limit=limit, offset=offset, user_id=user_id)
    return BaseResponse(
        success=True,
        message=f"Retrieved {history.total} evaluation record(s).",
        data=history,
    )


@router.get(
    "/summary",
    response_model=BaseResponse[EvaluationSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Evaluation Summary & Charts Telemetry",
    description="Retrieve aggregated quality, retrieval, performance, provider comparison, and chart trend telemetry.",
)
def get_evaluation_summary(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database_session),
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
) -> BaseResponse[EvaluationSummaryResponse]:
    summary = evaluation_service.get_summary(db, user_id=user_id)
    return BaseResponse(
        success=True,
        message="Evaluation telemetry summary aggregated successfully.",
        data=summary,
    )


@router.post(
    "/run",
    response_model=BaseResponse[BenchmarkRunResponse],
    status_code=status.HTTP_200_OK,
    summary="Run Automated RAG Benchmark Suite",
    description="Execute ground-truth benchmark dataset (50+ queries) and persist evaluation metrics.",
)
def run_benchmark_suite(
    request: BenchmarkRunRequest = BenchmarkRunRequest(),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database_session),
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
    retriever: Any = Depends(get_retriever),
    reranker: Any = Depends(get_reranker),
    provider_manager: Any = Depends(get_provider_manager),
) -> BaseResponse[BenchmarkRunResponse]:
    try:
        result = evaluation_service.run_benchmark(
            db=db,
            user_id=user_id,
            dataset_name=request.dataset_name,
            max_queries=request.max_queries,
            retriever=retriever,
            reranker=reranker,
            provider_manager=provider_manager,
            use_live_llm=request.use_live_llm,
        )
        return BaseResponse(
            success=True,
            message=f"Benchmark '{result.run_id}' completed across {result.total_queries} queries.",
            data=result,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/export",
    status_code=status.HTTP_200_OK,
    summary="Export Evaluation Report (CSV, JSON, PDF)",
    description="Download a formatted evaluation report containing executive summary, metrics, charts, and metadata.",
)
def export_evaluation_report(
    format: str = Query(default="json", pattern="^(csv|json|pdf)$", description="Export format: csv, json, or pdf"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database_session),
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
) -> Response:
    payload_bytes, media_type, filename = evaluation_service.export_report(db, fmt=format, user_id=user_id)
    return Response(
        content=payload_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


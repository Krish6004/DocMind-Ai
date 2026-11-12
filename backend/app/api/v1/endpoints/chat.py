"""
Chat and RAG completion endpoints for DocMind AI (Sprint 4.3).
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, status
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.deps import (
    get_chat_service,
    get_database_session,
    get_evaluation_service,
)
from backend.app.schemas.chat import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponseData,
)
from backend.app.schemas.common import BaseResponse
from backend.app.services.chat_service import ChatService
from backend.app.services.evaluation_service import EvaluationService

router = APIRouter()


def _observe_and_evaluate(
    evaluation_service: EvaluationService,
    db_bind: object,
    obs: dict,
) -> None:
    """Background observer that evaluates completed chat turns without blocking responses."""
    try:
        LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=db_bind)
        with LocalSession() as eval_db:
            evaluation_service.evaluate_and_persist(eval_db, **obs)
    except Exception:
        # Observer failures must never affect user chat execution
        pass


@router.post(
    "",
    response_model=BaseResponse[ChatResponseData],
    status_code=status.HTTP_200_OK,
    summary="Chat & RAG Query",
    description=(
        "Execute a grounded question-answering query against the document knowledge base. "
        "Flow: HybridRetriever (Dense + BM25 RRF) -> CrossEncoder Reranking -> "
        "Conversation Memory from SQLite -> LLM Generator. "
        "Saves interaction turn to SQLite and returns answer, sources, confidence, and latencies."
    ),
)
async def chat_completion(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database_session),
    chat_service: ChatService = Depends(get_chat_service),
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
) -> BaseResponse[ChatResponseData]:
    """
    Generate grounded answer for user query with citations and explainability metrics.
    """
    result = await chat_service.execute_chat(request=request, db=db)
    obs = getattr(chat_service, "last_observation", None)
    if obs and evaluation_service is not None:
        background_tasks.add_task(_observe_and_evaluate, evaluation_service, db.get_bind(), obs)

    return BaseResponse(
        success=True,
        message="Answer generated successfully.",
        data=result,
    )


@router.get(
    "/history/{session_id}",
    response_model=BaseResponse[ChatHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Chat History by Session",
    description="Retrieve all chronological conversation turns and retrieval metadata for a given session ID.",
)
def get_chat_history(
    session_id: str = Path(..., description="Conversation session UUID"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of historical turns to return"),
    db: Session = Depends(get_database_session),
    chat_service: ChatService = Depends(get_chat_service),
) -> BaseResponse[ChatHistoryResponse]:
    """
    Retrieve conversational history for multi-turn thread reconstruction.
    """
    history = chat_service.get_session_history(db=db, session_id=session_id, limit=limit)
    return BaseResponse(
        success=True,
        message=f"Retrieved {history.total_turns} conversation turn(s) for session '{session_id}'.",
        data=history,
    )

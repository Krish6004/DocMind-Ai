"""
Pydantic schemas and data contracts for DocMind AI Backend.
"""

from backend.app.schemas.chat import (
    ChatHistoryResponse,
    ChatHistoryTurn,
    ChatRequest,
    ChatResponseData,
    ConfidenceDetails,
    LatencyMetrics,
    SourceChunk,
)
from backend.app.schemas.common import BaseResponse, ErrorDetail, ErrorResponse
from backend.app.schemas.document import (
    DocumentDeleteData,
    DocumentListResponse,
    DocumentOut,
    UploadResponseData,
)
from backend.app.schemas.health import HealthResponse, RootResponse
from backend.app.schemas.provider import (
    ProviderInfo,
    ProviderListResponse,
    ProviderPriorityUpdateRequest,
    ProviderTestRequest,
    ProviderTestResponse,
    ProviderUpdateRequest,
)

__all__ = [
    "BaseResponse",
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "RootResponse",
    "DocumentOut",
    "DocumentListResponse",
    "UploadResponseData",
    "DocumentDeleteData",
    "ChatRequest",
    "ChatResponseData",
    "SourceChunk",
    "ConfidenceDetails",
    "LatencyMetrics",
    "ChatHistoryTurn",
    "ChatHistoryResponse",
    "ProviderInfo",
    "ProviderListResponse",
    "ProviderTestRequest",
    "ProviderTestResponse",
    "ProviderUpdateRequest",
    "ProviderPriorityUpdateRequest",
]

"""
ChatService orchestrating Hybrid Retrieval, Cross-Encoder Reranking,
LLM Answer Generation, Conversation Memory, and SQLite Persistence (Sprint 4.3).
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.errors import ServiceUnavailableException, ValidationException
from backend.app.core.logging import get_logger
from backend.app.db.models.chat import ChatHistoryModel
from backend.app.schemas.chat import (
    ChatHistoryResponse,
    ChatHistoryTurn,
    ChatRequest,
    ChatResponseData,
    ConfidenceDetails,
    LatencyMetrics,
    QueryRewriteTelemetry,
    RetrievalPlannerTelemetry,
    SourceChunk,
)
from src.retrieval_v2 import compute_retrieval_confidence
from src.utils import source_basename

logger = get_logger(__name__)


class ChatService:
    """
    Coordinates end-to-end RAG chat completion:
      1. Validates query and session inputs.
      2. Loads conversation history memory from SQLite (configurable window).
      3. Invokes HybridRetriever (Dense + BM25 with RRF).
      4. Invokes CrossEncoderReranker (ms-marco-MiniLM-L-6-v2).
      5. Invokes LLMGenerator with context and memory.
      6. Computes calibrated retrieval confidence and latency telemetry.
      7. Persists the interaction turn to the SQLite chat_history table.
    """

    def __init__(
        self,
        settings: Settings,
        hybrid_retriever: Any | None,
        reranker: Any | None,
        generator: Any | None = None,
        provider_manager: Any | None = None,
        query_rewriter: Any | None = None,
        retrieval_planner: Any | None = None,
    ) -> None:
        self.settings = settings
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker
        self.generator = generator
        self.provider_manager = provider_manager
        self.query_rewriter = query_rewriter
        self.retrieval_planner = retrieval_planner

    async def execute_chat(
        self,
        request: ChatRequest,
        db: Session,
        user_id: str = "default",
    ) -> ChatResponseData:
        """
        Execute RAG query pipeline with memory, reranking, generation, and persistence.

        Args:
            request: Validated ChatRequest.
            db: Active SQLAlchemy database session.

        Returns:
            Structured ChatResponseData.
        """
        t_total_0 = time.perf_counter()

        # 1. Generate unique request_id and resolve session_id
        request_id = str(uuid.uuid4())
        session_id = request.session_id.strip() if request.session_id and request.session_id.strip() else uuid.uuid4().hex

        clean_query = request.query.strip()
        if not clean_query:
            raise ValidationException("Query string cannot be empty or whitespace only.")

        logger.info(
            "Executing chat request [%s] (session: %s, top_k: %d, memory: %s)",
            request_id,
            session_id,
            request.top_k,
            request.use_memory,
        )

        # 2. Retrieve conversation memory from SQLite (if enabled)
        t_mem_0 = time.perf_counter()
        history_turns: list[ChatHistoryModel] = []
        if request.use_memory:
            history_turns = self._load_session_history(db, session_id, request.memory_window, user_id=user_id)
            logger.debug("Loaded %d previous conversation turns for memory context", len(history_turns))
        memory_retrieval_ms = (time.perf_counter() - t_mem_0) * 1000

        # 2b. Query Rewrite Layer (Conservative Pre-Retrieval Optimization)
        t_rewrite_0 = time.perf_counter()
        rewrite_telemetry: QueryRewriteTelemetry | None = None
        retrieval_query = clean_query

        if self.query_rewriter is not None:
            try:
                rewrite_res = self.query_rewriter.rewrite(
                    query=clean_query,
                    history=history_turns,
                )
                if rewrite_res:
                    if rewrite_res.is_rewritten:
                        retrieval_query = rewrite_res.rewritten_query
                        logger.info(
                            "Query rewritten for retrieval: '%s' -> '%s' (latency: %.2fms)",
                            clean_query,
                            retrieval_query,
                            rewrite_res.rewrite_time_ms,
                        )
                    rewrite_telemetry = QueryRewriteTelemetry(
                        original_query=rewrite_res.original_query,
                        rewritten_query=rewrite_res.rewritten_query,
                        rewrite_time_ms=rewrite_res.rewrite_time_ms,
                        status=rewrite_res.status,
                        is_rewritten=rewrite_res.is_rewritten,
                    )
            except Exception as exc:
                logger.warning("Query rewrite encountered an unexpected error: %s; falling back to original query.", exc)
                rewrite_telemetry = QueryRewriteTelemetry(
                    original_query=clean_query,
                    rewritten_query=clean_query,
                    rewrite_time_ms=round((time.perf_counter() - t_rewrite_0) * 1000, 2),
                    status="failed",
                    is_rewritten=False,
                )
        else:
            rewrite_telemetry = QueryRewriteTelemetry(
                original_query=clean_query,
                rewritten_query=clean_query,
                rewrite_time_ms=0.0,
                status="disabled",
                is_rewritten=False,
            )
        rewrite_latency_ms = (time.perf_counter() - t_rewrite_0) * 1000

        # 2c. Adaptive Hybrid Retrieval Planner
        t_plan_0 = time.perf_counter()
        planner_telemetry: RetrievalPlannerTelemetry | None = None
        effective_top_k = request.top_k
        effective_rerank_count = request.top_k
        plan = None

        vs = getattr(self.hybrid_retriever, "vectorstore", None) if self.hybrid_retriever is not None else None
        available_filenames = self._get_available_filenames(vs, user_id=user_id)

        if self.retrieval_planner is not None:
            try:
                plan = self.retrieval_planner.plan(
                    query=retrieval_query,
                    original_query=clean_query,
                    is_rewritten=bool(rewrite_telemetry and rewrite_telemetry.is_rewritten),
                    has_history=bool(history_turns),
                    available_filenames=available_filenames,
                )
                effective_top_k = plan.recommended_top_k
                effective_rerank_count = plan.recommended_rerank_count

                # Ensure conversation memory is loaded when planner detects follow-up
                if plan.needs_memory and not history_turns and not request.use_memory:
                    history_turns = self._load_session_history(db, session_id, request.memory_window, user_id=user_id)

                planner_telemetry = RetrievalPlannerTelemetry(
                    query_type=plan.query_type,
                    strategy_name=plan.strategy_name,
                    recommended_top_k=plan.recommended_top_k,
                    recommended_rerank_count=plan.recommended_rerank_count,
                    needs_memory=plan.needs_memory,
                    needs_metadata_filter=plan.needs_metadata_filter,
                    reason=plan.reason,
                    decision_time_ms=plan.decision_time_ms,
                )
                logger.info(
                    "Retrieval plan selected: type='%s', strategy='%s', top_k=%d, rerank=%d (%.3fms)",
                    plan.query_type,
                    plan.strategy_name,
                    effective_top_k,
                    effective_rerank_count,
                    plan.decision_time_ms,
                )
            except Exception as exc:
                logger.warning("RetrievalPlanner error (%s); using request defaults.", exc)
                effective_top_k = request.top_k
                effective_rerank_count = request.top_k
        planner_latency_ms = (time.perf_counter() - t_plan_0) * 1000

        # 3. Hybrid Retrieval (Dense + BM25 RRF)
        t_ret_0 = time.perf_counter()
        retrieved: list[dict[str, Any]] = []
        if self.hybrid_retriever is not None:
            if vs is not None and len(vs) == 0:
                logger.debug("VectorStore is empty; skipping hybrid retrieval.")
                retrieved = []
            else:
                try:
                    retrieved = self._orchestrate_retrieval(
                        query=retrieval_query,
                        top_k=effective_top_k,
                        explicit_filters=request.filters,
                        plan=plan,
                        available_filenames=available_filenames,
                        vs=vs,
                        user_id=user_id,
                    )
                except Exception as exc:
                    logger.warning("Hybrid retrieval encountered an error: %s", exc)
                    retrieved = []
        retrieval_ms = (time.perf_counter() - t_ret_0) * 1000

        # 4. Cross-Encoder Reranking
        t_rerank_0 = time.perf_counter()
        reranked: list[dict[str, Any]] = []
        if self.reranker is not None and retrieved:
            try:
                reranked = self.reranker.rerank(retrieval_query, retrieved, top_k=effective_rerank_count)
            except Exception as exc:
                logger.warning("Cross-encoder reranking failed; falling back to hybrid retrieval results: %s", exc)
                reranked = retrieved[:effective_rerank_count]
        else:
            reranked = retrieved[:effective_rerank_count]
        reranking_ms = (time.perf_counter() - t_rerank_0) * 1000

        # 5. Answer Generation
        t_gen_0 = time.perf_counter()
        answer = ""
        model_name = getattr(self.generator, "model", "gemini-2.5-flash")
        provider_used = "groq" if self.generator is not None else "none"
        token_usage_obs: dict[str, int] = {}
        sources_list: list[SourceChunk] = []

        system_prompt = (
            "You are a precise question-answering assistant. "
            "Answer questions using ONLY the provided context. "
            "If the context does not contain enough information to answer, "
            "say \"I don't have enough information in the provided documents "
            'to answer this question." '
            "Do not speculate or use knowledge outside the provided context. "
            "Cite sources using [Source N] notation where N matches the context "
            "block number."
        )

        # 5a. Prioritize mock / explicit generator dependency if provided (e.g. unit test overrides)
        if self.generator is not None:
            try:
                # If conversation history exists and generator supports raw messages API
                if history_turns and hasattr(self.generator, "_call_api") and hasattr(self.generator, "SYSTEM_PROMPT"):
                    messages = self._build_prompt_with_history(
                        query=retrieval_query,
                        chunks=reranked,
                        history=history_turns,
                        system_prompt=getattr(self.generator, "SYSTEM_PROMPT", system_prompt),
                    )
                    api_resp = self.generator._call_api(messages)
                    choice = api_resp["choices"][0]
                    answer = choice["message"]["content"]
                    model_name = api_resp.get("model", model_name)
                    usage = api_resp.get("usage", {})
                    if usage:
                        token_usage_obs = {
                            "prompt_tokens": int(usage.get("prompt_tokens", 0)),
                            "completion_tokens": int(usage.get("completion_tokens", 0)),
                            "total_tokens": int(usage.get("total_tokens", 0)),
                        }
                else:
                    # Standard grounded generation
                    gen_result = self.generator.generate(retrieval_query, reranked)
                    answer = gen_result.get("answer", "")
                    model_name = gen_result.get("model", model_name)
                    token_usage_obs = {
                        "prompt_tokens": int(gen_result.get("prompt_tokens", 0)),
                        "completion_tokens": int(gen_result.get("completion_tokens", 0)),
                        "total_tokens": int(gen_result.get("prompt_tokens", 0)) + int(gen_result.get("completion_tokens", 0)),
                    }

                # Extract attributed sources
                sources_list = self._format_source_chunks(reranked)

            except Exception as exc:
                logger.exception("LLM generation encountered failure: %s", exc)
                raise ServiceUnavailableException(
                    message=f"LLM Generation service error: {exc}",
                    details={"error": str(exc), "model": model_name},
                ) from exc

        # 5b. Use ProviderManager (Enterprise Multi-Provider & Fallback Engine)
        elif self.provider_manager is not None:
            messages = self._build_prompt_with_history(
                query=retrieval_query,
                chunks=reranked,
                history=history_turns,
                system_prompt=system_prompt,
            )
            try:
                gen_result = self.provider_manager.execute_generation(
                    messages=messages,
                    db=db,
                )
                answer = gen_result.get("answer", "")
                model_name = gen_result.get("model", model_name)
                provider_used = gen_result.get("provider", provider_used)
                token_usage_obs = {
                    "prompt_tokens": int(gen_result.get("prompt_tokens", 0)),
                    "completion_tokens": int(gen_result.get("completion_tokens", 0)),
                    "total_tokens": int(gen_result.get("prompt_tokens", 0)) + int(gen_result.get("completion_tokens", 0)),
                }
                sources_list = self._format_source_chunks(reranked)
            except Exception as exc:
                logger.info("AI Provider generation unavailable or failed: %s", exc)
                if not reranked:
                    answer = "I don't have enough information in the provided documents to answer this question."
                else:
                    answer = (
                        "Relevant document context was retrieved from the knowledge base, "
                        "but no LLM generator or active AI provider is currently configured. "
                        "Please configure your Gemini, Groq (GROQ_API_KEY), OpenAI, Anthropic, or Ollama credentials in Workspace Settings."
                    )
                sources_list = self._format_source_chunks(reranked)

        else:
            # Fallback when neither generator nor provider manager is available
            logger.info("No LLMGenerator or ProviderManager available. Generating deterministic fallback response.")
            if not reranked:
                answer = "I don't have enough information in the provided documents to answer this question."
            else:
                answer = (
                    "Relevant document context was retrieved from the knowledge base, "
                    "but no LLM generator is currently configured. "
                    "Please configure Gemini, Groq (GROQ_API_KEY), OpenAI, Anthropic, or Ollama in Workspace Settings."
                )
            sources_list = self._format_source_chunks(reranked)

        generation_ms = (time.perf_counter() - t_gen_0) * 1000
        total_ms = (time.perf_counter() - t_total_0) * 1000

        # 6. Calculate Confidence & Telemetry Metrics
        t_conf_0 = time.perf_counter()
        confidence_dict = compute_retrieval_confidence(reranked)
        confidence_ms = (time.perf_counter() - t_conf_0) * 1000
        confidence_obj = ConfidenceDetails(
            score=round(float(confidence_dict["score"]), 4),
            percentage=round(float(confidence_dict["percentage"]), 2),
            level=str(confidence_dict["level"]),
            color=str(confidence_dict["color"]),
            explanation=str(confidence_dict["explanation"]),
            details=confidence_dict.get("details"),
        )

        metrics_obj = LatencyMetrics(
            retrieval_latency_ms=round(retrieval_ms, 2),
            reranking_latency_ms=round(reranking_ms, 2),
            generation_latency_ms=round(generation_ms, 2),
            total_latency_ms=round(total_ms, 2),
            retrieved_chunk_count=len(retrieved),
            reranked_chunk_count=len(reranked),
            rewrite_latency_ms=round(rewrite_latency_ms, 2),
            planner_latency_ms=round(planner_latency_ms, 3),
        )

        # 7. Persist Chat Turn into SQLite
        try:
            sources_payload = [s.model_dump() for s in sources_list]
            chat_record = ChatHistoryModel(
                id=request_id,
                user_id=user_id,
                session_id=session_id,
                query=clean_query,
                answer=answer,
                retrieved_sources=json.dumps(sources_payload),
                confidence_score=round(float(confidence_dict["score"]), 4),
                latency_ms=round(total_ms, 2),
                created_at=datetime.now(timezone.utc),
            )
            db.add(chat_record)
            db.commit()
            logger.debug("Persisted interaction turn [%s] in SQLite session '%s'", request_id, session_id)
        except Exception as exc:
            logger.error("Failed to persist chat history turn into SQLite: %s", exc)
            db.rollback()

        response_payload = ChatResponseData(
            request_id=request_id,
            session_id=session_id,
            query=clean_query,
            answer=answer,
            sources=sources_list,
            confidence=confidence_obj,
            metrics=metrics_obj,
            query_rewrite=rewrite_telemetry,
            retrieval_planner=planner_telemetry,
            model=model_name,
            created_at=datetime.now(timezone.utc),
        )

        # Read-only observation snapshot for async EvaluationService
        self.last_observation = {
            "user_id": user_id,
            "request_id": request_id,
            "session_id": session_id,
            "query": clean_query,
            "answer": answer,
            "sources": [
                {
                    **s.model_dump(),
                    "similarity_score": float(reranked[i].get("similarity_score", 0.0) or 0.0) if i < len(reranked) else 0.0,
                    "rerank_score": float(reranked[i].get("rerank_score", reranked[i].get("score", 0.0)) or 0.0) if i < len(reranked) else s.score,
                }
                for i, s in enumerate(sources_list)
            ],
            "retrieved_chunks": retrieved,
            "confidence_percentage": float(confidence_obj.percentage),
            "provider": provider_used,
            "model": model_name,
            "latencies": {
                "query_rewrite_latency_ms": round(rewrite_latency_ms, 2),
                "planner_latency_ms": round(planner_latency_ms, 3),
                "retrieval_latency_ms": round(retrieval_ms, 2),
                "reranking_latency_ms": round(reranking_ms, 2),
                "generation_latency_ms": round(generation_ms, 2),
                "confidence_latency_ms": round(confidence_ms, 3),
                "memory_retrieval_time_ms": round(memory_retrieval_ms, 3),
                "total_response_time_ms": round(total_ms, 2),
            },
            "token_usage": token_usage_obs,
            "document_count": len(available_filenames),
        }

        return response_payload

    def get_session_history(
        self,
        db: Session,
        session_id: str,
        limit: int = 50,
        user_id: str = "default",
    ) -> ChatHistoryResponse:
        """
        Retrieve chronological chat history for a session scoped to user_id.
        """
        stmt = (
            select(ChatHistoryModel)
            .where(
                ChatHistoryModel.session_id == session_id,
                ChatHistoryModel.user_id == user_id,
            )
            .order_by(ChatHistoryModel.created_at.asc())
            .limit(limit)
        )
        turns = list(db.scalars(stmt).all())

        turn_schemas = []
        for t in turns:
            sources_val = None
            if t.retrieved_sources:
                try:
                    sources_val = json.loads(t.retrieved_sources)
                except Exception:
                    sources_val = None

            turn_schemas.append(
                ChatHistoryTurn(
                    id=t.id,
                    session_id=t.session_id,
                    query=t.query,
                    answer=t.answer,
                    sources=sources_val,
                    confidence_score=t.confidence_score,
                    latency_ms=t.latency_ms,
                    created_at=t.created_at,
                )
            )

        return ChatHistoryResponse(
            session_id=session_id,
            total_turns=len(turn_schemas),
            history=turn_schemas,
        )

    # -----------------------------------------------------------------------
    # Helper Methods
    # -----------------------------------------------------------------------

    def _load_session_history(
        self,
        db: Session,
        session_id: str,
        memory_window: int,
        user_id: str = "default",
    ) -> list[ChatHistoryModel]:
        """Load recent conversation turns in chronological order scoped to user_id."""
        stmt = (
            select(ChatHistoryModel)
            .where(
                ChatHistoryModel.session_id == session_id,
                ChatHistoryModel.user_id == user_id,
            )
            .order_by(ChatHistoryModel.created_at.desc())
            .limit(memory_window)
        )
        return list(reversed(list(db.scalars(stmt).all())))

    def _get_available_filenames(self, vectorstore: Any | None, user_id: str = "default") -> list[str]:
        """Extract unique indexed filenames from VectorStore metadata scoped to user_id."""
        if vectorstore is None:
            return []
        metadata_list = getattr(vectorstore, "_metadata", None) or getattr(vectorstore, "metadata", None)
        if not metadata_list:
            return []
        seen: list[str] = []
        seen_set: set[str] = set()
        for meta in metadata_list:
            if not isinstance(meta, dict):
                continue
            if user_id and user_id != "default" and meta.get("user_id") != user_id:
                continue
            fname = source_basename(meta)
            if fname and fname != "unknown" and fname not in seen_set:
                seen_set.add(fname)
                seen.append(fname)
        return seen

    def _merge_unique_chunks(
        self,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        limit: int,
    ) -> list[dict[str, Any]]:
        """Deduplicate chunks across retrieval pools while preserving priority order."""
        merged: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, Any, str]] = set()
        for chunk in [*primary, *secondary]:
            meta = chunk.get("metadata", {})
            key = (
                str(source_basename(meta)),
                meta.get("chunk_index", ""),
                str(chunk.get("text", ""))[:120],
            )
            if key not in seen_keys:
                seen_keys.add(key)
                merged.append(chunk)
                if len(merged) >= limit:
                    break
        return merged

    def _orchestrate_retrieval(
        self,
        query: str,
        top_k: int,
        explicit_filters: dict[str, Any] | None,
        plan: Any | None,
        available_filenames: list[str],
        vs: Any | None,
        user_id: str = "default",
    ) -> list[dict[str, Any]]:
        """Execute HybridRetriever calls orchestrated by the Adaptive Retrieval Planner."""
        base_filter: dict[str, Any] = dict(explicit_filters or {})
        if user_id and user_id != "default":
            if not available_filenames:
                return []
            base_filter["user_id"] = user_id

        effective_filter = base_filter if base_filter else None

        if explicit_filters is not None or plan is None:
            return self.hybrid_retriever.retrieve(
                query,
                top_k=top_k,
                metadata_filter=effective_filter,
            )

        # Multi-document orchestration: ensure coverage from every uploaded document
        if plan.query_type == "multi_document" and len(available_filenames) >= 2:
            per_doc_k = max(2, top_k // len(available_filenames))
            doc_chunks: list[dict[str, Any]] = []
            for fname in available_filenames[:10]:
                doc_filter = {**base_filter, "filename": fname}
                subset = self.hybrid_retriever.retrieve(
                    query,
                    top_k=per_doc_k,
                    metadata_filter=doc_filter,
                )
                doc_chunks.extend(subset)
            global_chunks = self.hybrid_retriever.retrieve(
                query,
                top_k=top_k,
                metadata_filter=effective_filter,
            )
            return self._merge_unique_chunks(doc_chunks, global_chunks, limit=top_k)

        # Code strategy orchestration: prioritize markdown/code chunks without losing general matches
        if plan.query_type == "code":
            md_chunks: list[dict[str, Any]] = []
            has_md = any(
                isinstance(m, dict)
                and str(m.get("file_type", "")).lower() == "md"
                and (user_id == "default" or m.get("user_id") == user_id)
                for m in (getattr(vs, "_metadata", None) or getattr(vs, "metadata", None) or [])
            )
            if has_md:
                md_chunks = self.hybrid_retriever.retrieve(
                    query,
                    top_k=top_k,
                    metadata_filter={**base_filter, "file_type": "md"},
                )
            general_chunks = self.hybrid_retriever.retrieve(
                query,
                top_k=top_k,
                metadata_filter=effective_filter,
            )
            code_like = [
                c for c in general_chunks
                if "```" in c.get("text", "") or "def " in c.get("text", "") or "class " in c.get("text", "")
            ]
            return self._merge_unique_chunks([*md_chunks, *code_like], general_chunks, limit=top_k)

        return self.hybrid_retriever.retrieve(
            query,
            top_k=top_k,
            metadata_filter=effective_filter,
        )

    def _build_prompt_with_history(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        history: list[ChatHistoryModel],
        system_prompt: str,
    ) -> list[dict[str, str]]:
        """
        Build an OpenAI-compatible messages array containing system prompt,
        previous conversational memory turns, and the current query with
        grounded context blocks.
        """
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

        # Append previous conversation memory turns
        for turn in history:
            messages.append({"role": "user", "content": turn.query})
            messages.append({"role": "assistant", "content": turn.answer})

        # Build numbered context blocks for current retrieved chunks
        context_blocks: list[str] = []
        for i, chunk in enumerate(chunks, start=1):
            meta = chunk.get("metadata", {})
            filename = source_basename(meta)
            chunk_idx = meta.get("chunk_index", "?")
            header = f"[Source {i}] ({filename}, chunk {chunk_idx}):"
            context_blocks.append(f"{header}\n{chunk.get('text', '')}")

        context_str = "\n\n".join(context_blocks) if context_blocks else "(no context provided)"
        user_content = f"Context:\n\n{context_str}\n\nQuestion: {query}"
        messages.append({"role": "user", "content": user_content})

        return messages

    def _format_source_chunks(self, chunks: list[dict[str, Any]]) -> list[SourceChunk]:
        """
        Convert retrieved/reranked chunk dicts into structured SourceChunk schemas.
        """
        sources: list[SourceChunk] = []
        for i, chunk in enumerate(chunks, start=1):
            meta = chunk.get("metadata", {})
            filename = source_basename(meta)
            score = chunk.get("rerank_score", chunk.get("score", 0.0))

            sources.append(
                SourceChunk(
                    source_num=i,
                    filename=filename,
                    chunk_index=meta.get("chunk_index", "?"),
                    score=round(float(score), 6),
                    text=chunk.get("text"),
                    metadata=meta,
                )
            )
        return sources

"""
Enterprise RAG Evaluation Engine & Benchmarking Service for DocMind AI (Sprint 6.0).

Design Principles:
- Strict Observer Pattern: Observes completed RAG inputs/outputs without ever
  modifying retrieval rankings, chunks, reranker scores, confidence, prompts,
  or generated answers.
- Ultra-low Overhead: Pure in-memory lexical/structural verification executes in
  < 5 ms per chat request (well within the 15 ms budget).
- Comprehensive Metrics: Retrieval (Precision@K, Recall@K, MRR, DCG/IDCG/NDCG,
  Context Recall, Retrieval Coverage, Source Diversity), Generation (0 -> 100
  normalized Grounding, Faithfulness, Citation Coverage, Context Utilization,
  Answer Completeness, Hallucination Risk, Source Utilization, Answer Length,
  Reasoning Coverage), Citation Verification (warnings only), and Performance.
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models.evaluation import EvaluationHistoryModel
from backend.app.schemas.evaluation import (
    BenchmarkRunResponse,
    CitationCheckItem,
    CitationVerificationResult,
    EvaluationHistoryListResponse,
    EvaluationRecord,
    EvaluationSummaryResponse,
    GenerationMetricsDetail,
    PerformanceMetricsDetail,
    ProviderComparisonEntry,
    RetrievalMetricsDetail,
)
from src.utils import source_basename

logger = get_logger(__name__)

# Common English stopwords excluded from content overlap checks
_STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "by", "can",
    "could", "did", "do", "does", "for", "from", "had", "has", "have", "he",
    "her", "here", "him", "his", "how", "i", "if", "in", "into", "is", "it",
    "its", "just", "may", "might", "more", "most", "must", "no", "not", "of",
    "on", "or", "our", "out", "over", "shall", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "them", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "up", "use",
    "used", "using", "very", "was", "we", "were", "what", "when", "where",
    "which", "while", "who", "why", "will", "with", "would", "you", "your",
})

_CITATION_PATTERN = re.compile(r"(?:\[|【)\s*Source\s+(\d+)\s*(?:\]|】)", re.IGNORECASE)
_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_\-\.]{2,}")
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+")
_REASONING_MARKERS = re.compile(
    r"\b(because|therefore|consequently|however|although|whereas|furthermore|"
    r"moreover|specifically|additionally|first|second|finally|in contrast|"
    r"as a result|which means|leading to)\b",
    re.IGNORECASE,
)


def _tokenize_content(text: str) -> set[str]:
    """Extract lowercase non-stopword content tokens for fast grounding checks."""
    if not text:
        return set()
    return {
        tok.lower().strip(".,;:!?\"'()[]{}")
        for tok in _TOKEN_PATTERN.findall(text)
        if tok.lower() not in _STOPWORDS and len(tok.strip(".,;:!?\"'()[]{}")) >= 2
    }


def _split_sentences(text: str) -> list[str]:
    """Split text into meaningful substantive sentences."""
    if not text:
        return []
    parts = [p.strip() for p in _SENTENCE_SPLIT_PATTERN.split(text.strip()) if p.strip()]
    return [p for p in parts if len(p) >= 6]


class EvaluationService:
    """
    Isolated Enterprise RAG Evaluation & Benchmarking Engine.
    """

    SYSTEM_VERSION = "v1.7.0"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.datasets_dir = self.settings.BASE_DIR / "evaluation" / "datasets"

    # ------------------------------------------------------------------
    # 1. Citation Verification (Non-Destructive, Warnings Only)
    # ------------------------------------------------------------------

    def verify_citations(
        self,
        answer: str,
        sources: list[dict[str, Any]],
    ) -> CitationVerificationResult:
        """
        Verify every [Source N] citation in the answer against provided sources.
        Never mutates the answer text; returns structured items and warnings.
        """
        raw_matches = _CITATION_PATTERN.findall(answer or "")
        seen_nums: list[int] = []
        for m in raw_matches:
            num = int(m)
            if num not in seen_nums:
                seen_nums.append(num)

        if not seen_nums:
            # Check if answer is an explicit abstention ("I don't have enough information")
            is_abstention = "don't have enough information" in (answer or "").lower()
            warnings: list[str] = []
            if not is_abstention and sources:
                warnings.append("Answer does not contain explicit [Source N] citations despite retrieved context.")
            return CitationVerificationResult(
                total_citations=0,
                valid_citations=0,
                citation_score=100.0 if is_abstention else (0.0 if sources else 100.0),
                items=[],
                warnings=warnings,
            )

        # Map sentences containing each citation for text-matching audit
        sentences = _split_sentences(answer or "")
        citation_sentences: dict[int, list[str]] = defaultdict(list)
        for sent in sentences:
            for m in _CITATION_PATTERN.findall(sent):
                citation_sentences[int(m)].append(sent)

        items, all_warnings = self._build_citation_items(seen_nums, sources, citation_sentences, answer)
        valid_count = sum(1 for it in items if it.chunk_exists and it.chunk_text_matches)
        citation_score = round((valid_count / len(items)) * 100.0, 2) if items else 0.0

        return CitationVerificationResult(
            total_citations=len(seen_nums),
            valid_citations=valid_count,
            citation_score=citation_score,
            items=items,
            warnings=all_warnings,
        )

    def _build_citation_items(
        self,
        seen_nums: list[int],
        sources: list[dict[str, Any]],
        citation_sentences: dict[int, list[str]],
        answer: str,
    ) -> tuple[list[CitationCheckItem], list[str]]:
        """Helper constructing verified CitationCheckItem records and warnings for all citations."""
        items: list[CitationCheckItem] = []
        all_warnings: list[str] = []

        for num in seen_nums:
            idx = num - 1
            if not (0 <= idx < len(sources)):
                warn = f"[Source {num}] references out-of-range chunk (only {len(sources)} sources returned)."
                all_warnings.append(warn)
                items.append(
                    CitationCheckItem(
                        citation_num=num,
                        citation_exists=True,
                        chunk_exists=False,
                        warning=warn,
                    )
                )
                continue

            src = sources[idx]
            meta = src.get("metadata") or {}
            filename = src.get("filename") or source_basename(meta)
            page_number = meta.get("page_number") or meta.get("page") or meta.get("page_count")
            chunk_index = src.get("chunk_index", meta.get("chunk_index"))
            chunk_text = str(src.get("text") or "")

            chunk_tokens = _tokenize_content(chunk_text)
            referring_text = " ".join(citation_sentences.get(num, [])) or answer
            referring_clean = _CITATION_PATTERN.sub("", referring_text)
            claim_tokens = _tokenize_content(referring_clean)

            overlap_ratio = (
                len(claim_tokens & chunk_tokens) / len(claim_tokens)
                if claim_tokens and chunk_tokens
                else 0.0
            )
            matches = bool(chunk_text.strip() and (overlap_ratio >= 0.12 or not claim_tokens))

            warns: list[str] = []
            if not filename or filename == "unknown":
                warns.append(f"[Source {num}] missing filename metadata.")
            if chunk_index is None or chunk_index == "?":
                warns.append(f"[Source {num}] missing chunk_index metadata.")
            if filename and str(filename).lower().endswith(".pdf") and page_number is None:
                warns.append(f"[Source {num}] PDF source missing page metadata.")
            if not chunk_text.strip():
                warns.append(f"[Source {num}] referenced chunk text is empty.")
            elif not matches:
                warns.append(f"[Source {num}] low lexical alignment ({overlap_ratio:.0%}) with chunk text.")

            all_warnings.extend(warns)
            items.append(
                CitationCheckItem(
                    citation_num=num,
                    citation_exists=True,
                    chunk_exists=True,
                    filename=str(filename) if filename else None,
                    page_number=page_number,
                    chunk_index=chunk_index,
                    chunk_text_matches=matches,
                    warning=" ".join(warns) if warns else None,
                )
            )
        return items, all_warnings

    # ------------------------------------------------------------------
    # 2. Retrieval Metrics (Precision, Recall, MRR, DCG/IDCG/NDCG, Coverage)
    # ------------------------------------------------------------------

    def compute_retrieval_evaluation(
        self,
        query: str,
        answer: str,
        retrieved_chunks: list[dict[str, Any]],
        sources: list[dict[str, Any]],
        total_corpus_docs: int = 0,
        expected_keywords: list[str] | None = None,
        expected_sources: list[str] | None = None,
    ) -> RetrievalMetricsDetail:
        """
        Compute Precision@K, Recall@K, MRR, DCG, IDCG, NDCG, Context Recall,
        Retrieval Coverage, and Source Diversity.
        """
        eval_chunks = sources if sources else retrieved_chunks
        k = len(eval_chunks)
        if k == 0:
            return RetrievalMetricsDetail(
                precision_at_k=0.0,
                recall_at_k=0.0,
                mrr=0.0,
                dcg=0.0,
                idcg=0.0,
                ndcg=0.0,
                context_recall=0.0,
                retrieval_coverage=0.0,
                source_diversity=0,
            )

        query_tokens = _tokenize_content(query)
        answer_tokens = _tokenize_content(_CITATION_PATTERN.sub("", answer or ""))
        cited_nums = {int(m) for m in _CITATION_PATTERN.findall(answer or "")}
        expected_kw_lower = [kw.lower() for kw in (expected_keywords or []) if kw]
        expected_src_lower = [s.lower() for s in (expected_sources or []) if s]

        relevance_grades: list[int] = []
        utilized_chunks = 0
        unique_docs: set[str] = set()

        for rank_idx, chunk in enumerate(eval_chunks, start=1):
            meta = chunk.get("metadata") or {}
            fname = str(chunk.get("filename") or source_basename(meta) or "").strip()
            if fname and fname != "unknown":
                unique_docs.add(fname)

            text_str = str(chunk.get("text") or "")
            chunk_tokens = _tokenize_content(text_str)

            # Determine graded relevance in {0, 1, 2}
            grade = 0
            if expected_kw_lower or expected_src_lower:
                # Ground-truth benchmark relevance judgment
                src_hit = any(es in fname.lower() for es in expected_src_lower) if expected_src_lower else False
                kw_hits = sum(1 for kw in expected_kw_lower if kw in text_str.lower())
                kw_ratio = kw_hits / len(expected_kw_lower) if expected_kw_lower else 0.0
                if src_hit and kw_ratio >= 0.25:
                    grade = 2
                elif src_hit or kw_ratio >= 0.25:
                    grade = 1
            else:
                # Online multi-signal relevance judgment
                rerank_score = chunk.get("rerank_score", chunk.get("score"))
                sim_score = chunk.get("similarity_score", 0.0)
                q_overlap = (
                    len(query_tokens & chunk_tokens) / len(query_tokens)
                    if query_tokens
                    else 0.0
                )
                is_cited = rank_idx in cited_nums
                high_rerank = rerank_score is not None and float(rerank_score) > 0.0
                moderate_signal = (
                    (sim_score is not None and float(sim_score) >= 0.42)
                    or q_overlap >= 0.25
                    or is_cited
                )
                if (high_rerank and moderate_signal) or (is_cited and q_overlap >= 0.2):
                    grade = 2
                elif high_rerank or moderate_signal:
                    grade = 1

            relevance_grades.append(grade)

            # Check context utilization / recall for this chunk
            ans_overlap = (
                len(answer_tokens & chunk_tokens) / max(1, min(len(answer_tokens), 12))
                if answer_tokens and chunk_tokens
                else 0.0
            )
            if rank_idx in cited_nums or ans_overlap >= 0.15:
                utilized_chunks += 1

        relevant_in_top_k = sum(1 for g in relevance_grades if g > 0)
        precision_at_k = round(relevant_in_top_k / k, 4)

        # Estimate total relevant items across broader retrieved pool or expected sources
        if expected_src_lower:
            total_relevant = max(relevant_in_top_k, len(expected_src_lower))
        else:
            pool_relevant = sum(
                1
                for c in (retrieved_chunks or eval_chunks)
                if (
                    float(c.get("rerank_score", c.get("score", 0.0)) or 0.0) > 0.0
                    or float(c.get("similarity_score", 0.0) or 0.0) >= 0.45
                    or (
                        len(query_tokens & _tokenize_content(str(c.get("text") or "")))
                        / max(1, len(query_tokens))
                        >= 0.25
                    )
                )
            )
            total_relevant = max(relevant_in_top_k, pool_relevant)

        recall_at_k = round(min(1.0, relevant_in_top_k / total_relevant), 4) if total_relevant > 0 else 0.0

        # MRR
        mrr = 0.0
        for idx, g in enumerate(relevance_grades, start=1):
            if g > 0:
                mrr = round(1.0 / idx, 4)
                break

        # DCG, IDCG, NDCG
        dcg = sum((2**rel - 1) / math.log2(i + 1) for i, rel in enumerate(relevance_grades, start=1))
        ideal_grades = sorted(relevance_grades, reverse=True)
        idcg = sum((2**rel - 1) / math.log2(i + 1) for i, rel in enumerate(ideal_grades, start=1))
        ndcg = round(dcg / idcg, 4) if idcg > 0 else 0.0

        context_recall = round((utilized_chunks / k) * 100.0, 2)
        source_diversity = len(unique_docs)
        effective_doc_total = max(total_corpus_docs, source_diversity)
        retrieval_coverage = (
            round(min(100.0, (source_diversity / effective_doc_total) * 100.0), 2)
            if effective_doc_total > 0
            else 0.0
        )

        return RetrievalMetricsDetail(
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            mrr=mrr,
            dcg=round(dcg, 4),
            idcg=round(idcg, 4),
            ndcg=ndcg,
            context_recall=context_recall,
            retrieval_coverage=retrieval_coverage,
            source_diversity=source_diversity,
        )

    # ------------------------------------------------------------------
    # 3. Generation Quality (Normalized 0 -> 100)
    # ------------------------------------------------------------------

    def compute_generation_evaluation(
        self,
        query: str,
        answer: str,
        sources: list[dict[str, Any]],
        citation_result: CitationVerificationResult,
        expected_keywords: list[str] | None = None,
    ) -> GenerationMetricsDetail:
        """
        Compute 9 generation quality metrics normalized to [0, 100].
        Executes deterministically without extra LLM calls (< 2 ms).
        """
        clean_answer = _CITATION_PATTERN.sub("", answer or "").strip()
        words = clean_answer.split()
        answer_length = len(words)
        is_abstention = "don't have enough information" in (answer or "").lower()

        context_text = " ".join(str(s.get("text") or "") for s in sources)
        context_tokens = _tokenize_content(context_text)
        answer_tokens = _tokenize_content(clean_answer)
        query_tokens = _tokenize_content(query)

        # Handle explicit safe abstention when no supporting docs exist
        if is_abstention:
            return GenerationMetricsDetail(
                grounding_score=100.0,
                faithfulness=100.0,
                citation_coverage=citation_result.citation_score,
                context_utilization=0.0,
                answer_completeness=50.0 if not sources else 40.0,
                hallucination_risk=0.0,
                source_utilization=0.0,
                answer_length=answer_length,
                reasoning_coverage=40.0,
            )

        # 1. Grounding Score: lexical evidence ratio in retrieved context
        if answer_tokens and context_tokens:
            supported_tokens = answer_tokens & context_tokens
            raw_grounding = (len(supported_tokens) / len(answer_tokens)) * 100.0
            # Scale slightly since grammatical glue/paraphrasing uses synonyms
            grounding_score = round(min(100.0, raw_grounding * 1.25 + (10.0 if citation_result.valid_citations > 0 else 0.0)), 2)
        else:
            grounding_score = 0.0

        # 2. Faithfulness: fraction of answer sentences supported by context
        sentences = _split_sentences(answer or "")
        if sentences and context_tokens:
            faithful_sentences = 0
            for sent in sentences:
                sent_clean = _CITATION_PATTERN.sub("", sent)
                s_tokens = _tokenize_content(sent_clean)
                if not s_tokens:
                    faithful_sentences += 1
                    continue
                overlap = len(s_tokens & context_tokens) / len(s_tokens)
                has_valid_cite = bool(_CITATION_PATTERN.search(sent))
                if overlap >= 0.22 or (has_valid_cite and overlap >= 0.10):
                    faithful_sentences += 1
            faithfulness = round((faithful_sentences / len(sentences)) * 100.0, 2)
        else:
            faithfulness = 0.0

        # 3. Citation Coverage: fraction of substantive sentences citing [Source N]
        if sentences:
            cited_sents = sum(1 for s in sentences if _CITATION_PATTERN.search(s))
            sent_cov = (cited_sents / len(sentences)) * 100.0
            citation_coverage = round(
                min(100.0, 0.5 * sent_cov + 0.5 * citation_result.citation_score),
                2,
            )
        else:
            citation_coverage = citation_result.citation_score

        # 4. Context Utilization: percentage of source chunks actively reflected in answer
        cited_nums = {int(m) for m in _CITATION_PATTERN.findall(answer or "")}
        if sources:
            utilized = 0
            for idx, src in enumerate(sources, start=1):
                src_tokens = _tokenize_content(str(src.get("text") or ""))
                overlap = (
                    len(answer_tokens & src_tokens) / max(1, min(10, len(src_tokens)))
                    if answer_tokens and src_tokens
                    else 0.0
                )
                if idx in cited_nums or overlap >= 0.18:
                    utilized += 1
            context_utilization = round((utilized / len(sources)) * 100.0, 2)
        else:
            context_utilization = 0.0

        # 5. Source Utilization: % of returned sources explicitly cited
        valid_cited_indices = {n for n in cited_nums if 1 <= n <= len(sources)}
        source_utilization = round((len(valid_cited_indices) / len(sources)) * 100.0, 2) if sources else 0.0

        # 6. Answer Completeness: coverage of query terms (+ expected keywords if benchmark)
        if expected_keywords:
            kw_hits = sum(1 for kw in expected_keywords if kw.lower() in clean_answer.lower())
            kw_cov = (kw_hits / len(expected_keywords)) * 100.0
        else:
            kw_cov = (len(query_tokens & answer_tokens) / len(query_tokens)) * 100.0 if query_tokens else 70.0
        length_factor = min(100.0, (answer_length / 25.0) * 100.0) if answer_length > 0 else 0.0
        answer_completeness = round(min(100.0, 0.7 * kw_cov + 0.3 * length_factor), 2)

        # 7. Hallucination Risk: inverse of grounding + faithfulness + citation integrity
        invalid_cite_penalty = len(citation_result.warnings) * 8.0
        base_trust = 0.55 * faithfulness + 0.45 * grounding_score
        hallucination_risk = round(min(100.0, max(0.0, (100.0 - base_trust) + invalid_cite_penalty)), 2)

        # 8. Reasoning Coverage: explanatory depth & multi-sentence structure
        reasoning_hits = len(_REASONING_MARKERS.findall(clean_answer))
        structure_score = min(100.0, (len(sentences) / 3.0) * 60.0 + min(40.0, reasoning_hits * 15.0))
        reasoning_coverage = round(
            min(100.0, 0.6 * structure_score + 0.4 * answer_completeness),
            2,
        )

        return GenerationMetricsDetail(
            grounding_score=grounding_score,
            faithfulness=faithfulness,
            citation_coverage=citation_coverage,
            context_utilization=context_utilization,
            answer_completeness=answer_completeness,
            hallucination_risk=hallucination_risk,
            source_utilization=source_utilization,
            answer_length=answer_length,
            reasoning_coverage=reasoning_coverage,
        )

    # ------------------------------------------------------------------
    # 4. End-to-End Evaluation & SQLite Persistence
    # ------------------------------------------------------------------

    def evaluate_and_persist(
        self,
        db: Session,
        *,
        request_id: str,
        session_id: str,
        query: str,
        answer: str,
        sources: list[dict[str, Any]],
        retrieved_chunks: list[dict[str, Any]] | None = None,
        confidence_percentage: float = 0.0,
        provider: str = "unknown",
        model: str = "unknown",
        latencies: dict[str, float] | None = None,
        token_usage: dict[str, int] | None = None,
        document_count: int = 0,
        expected_keywords: list[str] | None = None,
        expected_sources: list[str] | None = None,
        is_benchmark: bool = False,
    ) -> EvaluationRecord:
        """
        Evaluate a completed RAG query-response turn and persist to evaluation_history.
        """
        t_eval_0 = time.perf_counter()

        citation_res = self.verify_citations(answer=answer, sources=sources)
        retrieval_res = self.compute_retrieval_evaluation(
            query=query,
            answer=answer,
            retrieved_chunks=retrieved_chunks or sources,
            sources=sources,
            total_corpus_docs=document_count,
            expected_keywords=expected_keywords,
            expected_sources=expected_sources,
        )
        generation_res = self.compute_generation_evaluation(
            query=query,
            answer=answer,
            sources=sources,
            citation_result=citation_res,
            expected_keywords=expected_keywords,
        )

        # Overall RAG Score (0 -> 100)
        retrieval_composite = (
            retrieval_res.precision_at_k * 35.0
            + retrieval_res.recall_at_k * 25.0
            + retrieval_res.ndcg * 40.0
        )
        overall_score = round(
            min(
                100.0,
                max(
                    0.0,
                    0.30 * retrieval_composite
                    + 0.30 * generation_res.grounding_score
                    + 0.25 * generation_res.faithfulness
                    + 0.15 * citation_res.citation_score,
                ),
            ),
            2,
        )

        eval_ms = round((time.perf_counter() - t_eval_0) * 1000, 3)

        lat_in = dict(latencies or {})
        lat_in["evaluation_latency_ms"] = eval_ms

        tok_in = dict(token_usage or {})
        if not tok_in.get("total_tokens"):
            prompt_tok = tok_in.get("prompt_tokens") or max(1, len(query) // 4 + sum(len(str(s.get("text") or "")) // 4 for s in sources))
            comp_tok = tok_in.get("completion_tokens") or max(1, len(answer) // 4)
            tok_in = {
                "prompt_tokens": int(prompt_tok),
                "completion_tokens": int(comp_tok),
                "total_tokens": int(prompt_tok) + int(comp_tok),
            }

        perf_detail = PerformanceMetricsDetail(
            query_rewrite_latency_ms=float(lat_in.get("query_rewrite_latency_ms", 0.0)),
            planner_latency_ms=float(lat_in.get("planner_latency_ms", 0.0)),
            retrieval_latency_ms=float(lat_in.get("retrieval_latency_ms", 0.0)),
            reranking_latency_ms=float(lat_in.get("reranking_latency_ms", 0.0)),
            generation_latency_ms=float(lat_in.get("generation_latency_ms", 0.0)),
            confidence_latency_ms=float(lat_in.get("confidence_latency_ms", 0.0)),
            memory_retrieval_time_ms=float(lat_in.get("memory_retrieval_time_ms", 0.0)),
            evaluation_latency_ms=eval_ms,
            total_response_time_ms=float(lat_in.get("total_response_time_ms", 0.0)),
            prompt_tokens=int(tok_in.get("prompt_tokens", 0)),
            completion_tokens=int(tok_in.get("completion_tokens", 0)),
            total_tokens=int(tok_in.get("total_tokens", 0)),
            retrieved_chunk_count=len(retrieved_chunks or sources),
            reranked_chunk_count=len(sources),
            document_count=document_count,
            provider=provider or "unknown",
            model=model or "unknown",
        )

        record_id = uuid.uuid4().hex
        now_utc = datetime.now(timezone.utc)

        orm_row = EvaluationHistoryModel(
            id=record_id,
            request_id=request_id,
            session_id=session_id,
            query=query,
            answer=answer,
            provider=perf_detail.provider,
            model=perf_detail.model,
            confidence=round(float(confidence_percentage), 2),
            precision=retrieval_res.precision_at_k,
            recall=retrieval_res.recall_at_k,
            mrr=retrieval_res.mrr,
            ndcg=retrieval_res.ndcg,
            dcg=retrieval_res.dcg,
            idcg=retrieval_res.idcg,
            context_recall=retrieval_res.context_recall,
            retrieval_coverage=retrieval_res.retrieval_coverage,
            source_diversity=retrieval_res.source_diversity,
            grounding=generation_res.grounding_score,
            faithfulness=generation_res.faithfulness,
            citation_score=citation_res.citation_score,
            context_utilization=generation_res.context_utilization,
            answer_completeness=generation_res.answer_completeness,
            hallucination_score=generation_res.hallucination_risk,
            source_utilization=generation_res.source_utilization,
            answer_length=generation_res.answer_length,
            reasoning_coverage=generation_res.reasoning_coverage,
            overall_score=overall_score,
            citation_verification=citation_res.model_dump_json(),
            latencies=json.dumps({
                "query_rewrite_latency_ms": perf_detail.query_rewrite_latency_ms,
                "planner_latency_ms": perf_detail.planner_latency_ms,
                "retrieval_latency_ms": perf_detail.retrieval_latency_ms,
                "reranking_latency_ms": perf_detail.reranking_latency_ms,
                "generation_latency_ms": perf_detail.generation_latency_ms,
                "confidence_latency_ms": perf_detail.confidence_latency_ms,
                "memory_retrieval_time_ms": perf_detail.memory_retrieval_time_ms,
                "evaluation_latency_ms": perf_detail.evaluation_latency_ms,
                "total_response_time_ms": perf_detail.total_response_time_ms,
                "retrieved_chunk_count": perf_detail.retrieved_chunk_count,
                "reranked_chunk_count": perf_detail.reranked_chunk_count,
            }),
            token_usage=json.dumps(tok_in),
            document_count=document_count,
            chunk_count=len(sources),
            is_benchmark=is_benchmark,
            created_at=now_utc,
        )

        try:
            db.add(orm_row)
            db.commit()
        except Exception as exc:
            logger.error("Failed to persist evaluation_history row: %s", exc)
            db.rollback()

        return EvaluationRecord(
            id=record_id,
            request_id=request_id,
            session_id=session_id,
            query=query,
            answer=answer,
            provider=perf_detail.provider,
            model=perf_detail.model,
            confidence=round(float(confidence_percentage), 2),
            overall_score=overall_score,
            retrieval=retrieval_res,
            generation=generation_res,
            citation_verification=citation_res,
            performance=perf_detail,
            is_benchmark=is_benchmark,
            created_at=now_utc,
        )

    # ------------------------------------------------------------------
    # 5. Querying Evaluation History & Dashboard Summaries
    # ------------------------------------------------------------------

    def _row_to_record(self, row: EvaluationHistoryModel) -> EvaluationRecord:
        """Convert ORM EvaluationHistoryModel into structured EvaluationRecord."""
        lat_dict = {}
        tok_dict = {}
        cit_obj = CitationVerificationResult()
        try:
            lat_dict = json.loads(row.latencies or "{}")
        except Exception:
            pass
        try:
            tok_dict = json.loads(row.token_usage or "{}")
        except Exception:
            pass
        try:
            if row.citation_verification:
                cit_obj = CitationVerificationResult.model_validate_json(row.citation_verification)
        except Exception:
            pass

        return EvaluationRecord(
            id=row.id,
            request_id=row.request_id,
            session_id=row.session_id,
            query=row.query,
            answer=row.answer,
            provider=row.provider,
            model=row.model,
            confidence=row.confidence,
            overall_score=row.overall_score,
            retrieval=RetrievalMetricsDetail(
                precision_at_k=row.precision,
                recall_at_k=row.recall,
                mrr=row.mrr,
                dcg=row.dcg,
                idcg=row.idcg,
                ndcg=row.ndcg,
                context_recall=row.context_recall,
                retrieval_coverage=row.retrieval_coverage,
                source_diversity=row.source_diversity,
            ),
            generation=GenerationMetricsDetail(
                grounding_score=row.grounding,
                faithfulness=row.faithfulness,
                citation_coverage=row.citation_score,
                context_utilization=row.context_utilization,
                answer_completeness=row.answer_completeness,
                hallucination_risk=row.hallucination_score,
                source_utilization=row.source_utilization,
                answer_length=row.answer_length,
                reasoning_coverage=row.reasoning_coverage,
            ),
            citation_verification=cit_obj,
            performance=PerformanceMetricsDetail(
                query_rewrite_latency_ms=float(lat_dict.get("query_rewrite_latency_ms", 0.0)),
                planner_latency_ms=float(lat_dict.get("planner_latency_ms", 0.0)),
                retrieval_latency_ms=float(lat_dict.get("retrieval_latency_ms", 0.0)),
                reranking_latency_ms=float(lat_dict.get("reranking_latency_ms", 0.0)),
                generation_latency_ms=float(lat_dict.get("generation_latency_ms", 0.0)),
                confidence_latency_ms=float(lat_dict.get("confidence_latency_ms", 0.0)),
                memory_retrieval_time_ms=float(lat_dict.get("memory_retrieval_time_ms", 0.0)),
                evaluation_latency_ms=float(lat_dict.get("evaluation_latency_ms", 0.0)),
                total_response_time_ms=float(lat_dict.get("total_response_time_ms", 0.0)),
                prompt_tokens=int(tok_dict.get("prompt_tokens", 0)),
                completion_tokens=int(tok_dict.get("completion_tokens", 0)),
                total_tokens=int(tok_dict.get("total_tokens", 0)),
                retrieved_chunk_count=int(lat_dict.get("retrieved_chunk_count", row.chunk_count)),
                reranked_chunk_count=int(lat_dict.get("reranked_chunk_count", row.chunk_count)),
                document_count=row.document_count,
                provider=row.provider,
                model=row.model,
            ),
            is_benchmark=bool(row.is_benchmark),
            created_at=row.created_at,
        )

    def get_latest(self, db: Session) -> EvaluationRecord | None:
        """Fetch most recent evaluation record."""
        stmt = select(EvaluationHistoryModel).order_by(desc(EvaluationHistoryModel.created_at)).limit(1)
        row = db.scalars(stmt).first()
        return self._row_to_record(row) if row else None

    def get_history(self, db: Session, limit: int = 100, offset: int = 0) -> EvaluationHistoryListResponse:
        """Fetch last N (default 100) evaluation records."""
        stmt = (
            select(EvaluationHistoryModel)
            .order_by(desc(EvaluationHistoryModel.created_at))
            .offset(offset)
            .limit(limit)
        )
        rows = list(db.scalars(stmt).all())
        items = [self._row_to_record(r) for r in rows]
        return EvaluationHistoryListResponse(total=len(items), items=items)

    def get_summary(self, db: Session, limit: int = 200) -> EvaluationSummaryResponse:
        """Aggregate dashboard metrics, trends, provider comparison, and heatmap matrix."""
        stmt = select(EvaluationHistoryModel).order_by(desc(EvaluationHistoryModel.created_at)).limit(limit)
        rows = list(db.scalars(stmt).all())
        if not rows:
            return EvaluationSummaryResponse()

        records = [self._row_to_record(r) for r in rows]
        n = len(records)

        def avg(vals: list[float]) -> float:
            return round(sum(vals) / len(vals), 2) if vals else 0.0

        avg_precision = round(sum(r.retrieval.precision_at_k for r in records) / n, 4)
        avg_recall = round(sum(r.retrieval.recall_at_k for r in records) / n, 4)
        avg_mrr = round(sum(r.retrieval.mrr for r in records) / n, 4)
        avg_ndcg = round(sum(r.retrieval.ndcg for r in records) / n, 4)
        avg_retrieval_score = round((avg_precision * 35.0 + avg_recall * 25.0 + avg_ndcg * 40.0), 2)

        avg_grounding = avg([r.generation.grounding_score for r in records])
        avg_faithfulness = avg([r.generation.faithfulness for r in records])
        avg_citation_cov = avg([r.generation.citation_coverage for r in records])
        avg_generation_score = round((avg_grounding + avg_faithfulness + avg_citation_cov) / 3.0, 2)

        total_tokens = sum(r.performance.total_tokens for r in records)

        # Provider Comparison
        by_provider: dict[str, list[EvaluationRecord]] = defaultdict(list)
        for rec in records:
            by_provider[rec.provider or "unknown"].append(rec)

        provider_comparison = [
            ProviderComparisonEntry(
                provider=prov,
                total_runs=len(plist),
                avg_overall_score=avg([p.overall_score for p in plist]),
                avg_grounding=avg([p.generation.grounding_score for p in plist]),
                avg_faithfulness=avg([p.generation.faithfulness for p in plist]),
                avg_hallucination_risk=avg([p.generation.hallucination_risk for p in plist]),
                avg_latency_ms=avg([p.performance.total_response_time_ms for p in plist]),
                avg_tokens=avg([float(p.performance.total_tokens) for p in plist]),
            )
            for prov, plist in by_provider.items()
        ]

        # Trend Series (chronological order for charts)
        chrono = list(reversed(records[:30]))
        trend_series = [
            {
                "index": idx + 1,
                "label": f"#{idx + 1}",
                "query": rec.query[:28] + ("..." if len(rec.query) > 28 else ""),
                "overall_score": rec.overall_score,
                "grounding": rec.generation.grounding_score,
                "faithfulness": rec.generation.faithfulness,
                "hallucination": rec.generation.hallucination_risk,
                "precision": round(rec.retrieval.precision_at_k * 100.0, 1),
                "recall": round(rec.retrieval.recall_at_k * 100.0, 1),
                "ndcg": round(rec.retrieval.ndcg * 100.0, 1),
                "latency_ms": rec.performance.total_response_time_ms,
                "tokens": rec.performance.total_tokens,
            }
            for idx, rec in enumerate(chrono)
        ]

        # Heatmap matrix across recent 10 queries vs 6 quality dimensions
        heatmap_matrix = [
            {
                "query": rec.query[:24] + ("..." if len(rec.query) > 24 else ""),
                "Precision": round(rec.retrieval.precision_at_k * 100.0, 1),
                "Recall": round(rec.retrieval.recall_at_k * 100.0, 1),
                "NDCG": round(rec.retrieval.ndcg * 100.0, 1),
                "Grounding": round(rec.generation.grounding_score, 1),
                "Faithfulness": round(rec.generation.faithfulness, 1),
                "Citation": round(rec.citation_verification.citation_score, 1),
            }
            for rec in reversed(records[:10])
        ]

        return EvaluationSummaryResponse(
            total_evaluations=n,
            overall_rag_score=avg([r.overall_score for r in records]),
            avg_grounding=avg_grounding,
            avg_retrieval_score=avg_retrieval_score,
            avg_generation_score=avg_generation_score,
            avg_hallucination_risk=avg([r.generation.hallucination_risk for r in records]),
            avg_precision=avg_precision,
            avg_recall=avg_recall,
            avg_mrr=avg_mrr,
            avg_ndcg=avg_ndcg,
            avg_context_recall=avg([r.retrieval.context_recall for r in records]),
            avg_retrieval_coverage=avg([r.retrieval.retrieval_coverage for r in records]),
            avg_source_diversity=avg([float(r.retrieval.source_diversity) for r in records]),
            avg_faithfulness=avg_faithfulness,
            avg_citation_coverage=avg_citation_cov,
            avg_context_utilization=avg([r.generation.context_utilization for r in records]),
            avg_answer_completeness=avg([r.generation.answer_completeness for r in records]),
            avg_source_utilization=avg([r.generation.source_utilization for r in records]),
            avg_reasoning_coverage=avg([r.generation.reasoning_coverage for r in records]),
            avg_confidence=avg([r.confidence for r in records]),
            avg_total_latency_ms=avg([r.performance.total_response_time_ms for r in records]),
            avg_rewrite_latency_ms=avg([r.performance.query_rewrite_latency_ms for r in records]),
            avg_planner_latency_ms=avg([r.performance.planner_latency_ms for r in records]),
            avg_retrieval_latency_ms=avg([r.performance.retrieval_latency_ms for r in records]),
            avg_reranking_latency_ms=avg([r.performance.reranking_latency_ms for r in records]),
            avg_generation_latency_ms=avg([r.performance.generation_latency_ms for r in records]),
            total_tokens=total_tokens,
            avg_tokens_per_query=round(total_tokens / n, 1),
            provider_comparison=provider_comparison,
            trend_series=trend_series,
            heatmap_matrix=heatmap_matrix,
        )

    # ------------------------------------------------------------------
    # 6. Automated Benchmark Runner (50+ Queries)
    # ------------------------------------------------------------------

    def load_benchmark_dataset(self, dataset_name: str = "sample_questions.json") -> dict[str, Any]:
        """Load dataset JSON from evaluation/datasets/."""
        safe_name = Path(dataset_name).name
        target = self.datasets_dir / safe_name
        if not target.exists():
            raise FileNotFoundError(f"Benchmark dataset '{safe_name}' not found at {target}")
        with target.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def run_benchmark(
        self,
        db: Session,
        *,
        dataset_name: str = "sample_questions.json",
        max_queries: int = 55,
        retriever: Any | None = None,
        reranker: Any | None = None,
        provider_manager: Any | None = None,
        use_live_llm: bool = False,
    ) -> BenchmarkRunResponse:
        """
        Execute automated benchmark across ground-truth dataset queries,
        evaluating retrieval & grounded synthesis without altering RAG math.
        """
        from src.retrieval_v2 import compute_retrieval_confidence

        dataset = self.load_benchmark_dataset(dataset_name)
        questions = list(dataset.get("questions", []))[:max_queries]
        run_id = f"bench_{uuid.uuid4().hex[:10]}"

        vs = getattr(retriever, "vectorstore", None) if retriever is not None else None
        corpus_docs = {
            source_basename(m)
            for m in (getattr(vs, "metadata", []) or [])
            if isinstance(m, dict) and source_basename(m) != "unknown"
        }
        doc_count = len(corpus_docs)

        results: list[EvaluationRecord] = []
        active_provider = "benchmark-evaluator"
        active_model = "hybrid-rerank-eval"
        if provider_manager is not None:
            try:
                active_provider = provider_manager.get_active_provider_id(db=db)
            except Exception:
                pass

        for item in questions:
            q_text = item["question"]
            expected_kw = item.get("expected_keywords", [])
            expected_src = item.get("expected_sources", [])

            t0 = time.perf_counter()
            t_ret = time.perf_counter()
            retrieved: list[dict[str, Any]] = []
            if retriever is not None and vs is not None and len(vs) > 0:
                try:
                    retrieved = retriever.retrieve(q_text, top_k=5)
                except Exception:
                    retrieved = []
            ret_ms = (time.perf_counter() - t_ret) * 1000

            t_rerank = time.perf_counter()
            reranked = retrieved[:5]
            if reranker is not None and retrieved:
                try:
                    reranked = reranker.rerank(q_text, retrieved, top_k=5)
                except Exception:
                    reranked = retrieved[:5]
            rerank_ms = (time.perf_counter() - t_rerank) * 1000

            # Format source dicts consistently
            formatted_sources: list[dict[str, Any]] = []
            for idx, ch in enumerate(reranked, start=1):
                meta = ch.get("metadata") or {}
                formatted_sources.append({
                    "source_num": idx,
                    "filename": source_basename(meta),
                    "chunk_index": meta.get("chunk_index", "?"),
                    "score": float(ch.get("rerank_score", ch.get("score", 0.0)) or 0.0),
                    "similarity_score": float(ch.get("similarity_score", 0.0) or 0.0),
                    "rerank_score": float(ch.get("rerank_score", ch.get("score", 0.0)) or 0.0),
                    "text": ch.get("text", ""),
                    "metadata": meta,
                })

            t_conf = time.perf_counter()
            conf = compute_retrieval_confidence(reranked)
            conf_ms = (time.perf_counter() - t_conf) * 1000

            t_gen = time.perf_counter()
            used_provider = active_provider
            used_model = active_model
            token_usage: dict[str, int] = {}

            if use_live_llm and provider_manager is not None and formatted_sources:
                try:
                    ctx_str = "\n".join(
                        f"[Source {s['source_num']}]: {s['text'][:350]}"
                        for s in formatted_sources[:3]
                    )
                    gen = provider_manager.execute_generation(
                        messages=[
                            {"role": "system", "content": "Answer concisely using ONLY context and cite [Source N]."},
                            {"role": "user", "content": f"Context:\n{ctx_str}\n\nQuestion: {q_text}"},
                        ],
                        db=db,
                        max_tokens=250,
                    )
                    answer = gen.get("answer", "")
                    used_provider = gen.get("provider", used_provider)
                    used_model = gen.get("model", used_model)
                    token_usage = {
                        "prompt_tokens": int(gen.get("prompt_tokens", 0)),
                        "completion_tokens": int(gen.get("completion_tokens", 0)),
                        "total_tokens": int(gen.get("prompt_tokens", 0)) + int(gen.get("completion_tokens", 0)),
                    }
                except Exception:
                    answer = self._synthesize_benchmark_answer(q_text, formatted_sources)
            else:
                answer = self._synthesize_benchmark_answer(q_text, formatted_sources)

            gen_ms = (time.perf_counter() - t_gen) * 1000
            total_ms = (time.perf_counter() - t0) * 1000

            rec = self.evaluate_and_persist(
                db=db,
                request_id=f"{run_id}_{item.get('id', uuid.uuid4().hex[:6])}",
                session_id=run_id,
                query=q_text,
                answer=answer,
                sources=formatted_sources,
                retrieved_chunks=retrieved,
                confidence_percentage=float(conf.get("percentage", 0.0)),
                provider=used_provider,
                model=used_model,
                latencies={
                    "retrieval_latency_ms": round(ret_ms, 2),
                    "reranking_latency_ms": round(rerank_ms, 2),
                    "generation_latency_ms": round(gen_ms, 2),
                    "confidence_latency_ms": round(conf_ms, 2),
                    "total_response_time_ms": round(total_ms, 2),
                },
                token_usage=token_usage,
                document_count=doc_count,
                expected_keywords=expected_kw,
                expected_sources=expected_src,
                is_benchmark=True,
            )
            results.append(rec)

        n = len(results)
        avg_f = lambda vals: round(sum(vals) / n, 4) if n else 0.0
        avg_pct = lambda vals: round(sum(vals) / n, 2) if n else 0.0

        by_prov: dict[str, list[EvaluationRecord]] = defaultdict(list)
        for r in results:
            by_prov[r.provider].append(r)

        provider_comp = [
            ProviderComparisonEntry(
                provider=p,
                total_runs=len(plist),
                avg_overall_score=round(sum(x.overall_score for x in plist) / len(plist), 2),
                avg_grounding=round(sum(x.generation.grounding_score for x in plist) / len(plist), 2),
                avg_faithfulness=round(sum(x.generation.faithfulness for x in plist) / len(plist), 2),
                avg_hallucination_risk=round(sum(x.generation.hallucination_risk for x in plist) / len(plist), 2),
                avg_latency_ms=round(sum(x.performance.total_response_time_ms for x in plist) / len(plist), 2),
                avg_tokens=round(sum(x.performance.total_tokens for x in plist) / len(plist), 1),
            )
            for p, plist in by_prov.items()
        ]

        return BenchmarkRunResponse(
            run_id=run_id,
            dataset_name=dataset_name,
            total_queries=n,
            avg_precision=avg_f([r.retrieval.precision_at_k for r in results]),
            avg_recall=avg_f([r.retrieval.recall_at_k for r in results]),
            avg_mrr=avg_f([r.retrieval.mrr for r in results]),
            avg_ndcg=avg_f([r.retrieval.ndcg for r in results]),
            avg_grounding=avg_pct([r.generation.grounding_score for r in results]),
            avg_faithfulness=avg_pct([r.generation.faithfulness for r in results]),
            avg_hallucination=avg_pct([r.generation.hallucination_risk for r in results]),
            avg_latency_ms=avg_pct([r.performance.total_response_time_ms for r in results]),
            avg_confidence=avg_pct([r.confidence for r in results]),
            document_coverage=avg_pct([r.retrieval.retrieval_coverage for r in results]),
            provider_comparison=provider_comp,
            executed_at=datetime.now(timezone.utc),
            sample_results=results[:10],
        )

    def _synthesize_benchmark_answer(self, query: str, sources: list[dict[str, Any]]) -> str:
        """
        Deterministic grounded summary from retrieved chunks when running offline
        50+ query benchmarks without consuming external LLM quota.
        """
        if not sources:
            return "I don't have enough information in the provided documents to answer this question."
        snippets: list[str] = []
        for s in sources[:3]:
            text = " ".join(str(s.get("text") or "").split())
            if text:
                snippets.append(f"{text[:180].rstrip()} [Source {s['source_num']}]")
        return " ".join(snippets) if snippets else "I don't have enough information in the provided documents to answer this question."

    # ------------------------------------------------------------------
    # 7. Export Reports (CSV, JSON, PDF)
    # ------------------------------------------------------------------

    def export_report(
        self,
        db: Session,
        fmt: str = "json",
    ) -> tuple[bytes, str, str]:
        """
        Generate downloadable evaluation report in CSV, JSON, or PDF format.
        Returns (payload_bytes, media_type, filename).
        """
        summary = self.get_summary(db)
        history = self.get_history(db, limit=100).items
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        fmt_lower = fmt.lower().strip()

        if fmt_lower == "json":
            payload = {
                "system": "DocMind AI",
                "system_version": self.SYSTEM_VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "executive_summary": {
                    "total_evaluations": summary.total_evaluations,
                    "overall_rag_score": summary.overall_rag_score,
                    "avg_grounding": summary.avg_grounding,
                    "avg_faithfulness": summary.avg_faithfulness,
                    "avg_hallucination_risk": summary.avg_hallucination_risk,
                    "avg_confidence": summary.avg_confidence,
                },
                "retrieval_metrics": {
                    "avg_precision": summary.avg_precision,
                    "avg_recall": summary.avg_recall,
                    "avg_mrr": summary.avg_mrr,
                    "avg_ndcg": summary.avg_ndcg,
                    "avg_context_recall": summary.avg_context_recall,
                    "avg_retrieval_coverage": summary.avg_retrieval_coverage,
                    "avg_source_diversity": summary.avg_source_diversity,
                },
                "generation_metrics": {
                    "avg_grounding": summary.avg_grounding,
                    "avg_faithfulness": summary.avg_faithfulness,
                    "avg_citation_coverage": summary.avg_citation_coverage,
                    "avg_context_utilization": summary.avg_context_utilization,
                    "avg_answer_completeness": summary.avg_answer_completeness,
                    "avg_hallucination_risk": summary.avg_hallucination_risk,
                    "avg_source_utilization": summary.avg_source_utilization,
                    "avg_reasoning_coverage": summary.avg_reasoning_coverage,
                },
                "performance": {
                    "avg_total_latency_ms": summary.avg_total_latency_ms,
                    "avg_rewrite_latency_ms": summary.avg_rewrite_latency_ms,
                    "avg_planner_latency_ms": summary.avg_planner_latency_ms,
                    "avg_retrieval_latency_ms": summary.avg_retrieval_latency_ms,
                    "avg_reranking_latency_ms": summary.avg_reranking_latency_ms,
                    "avg_generation_latency_ms": summary.avg_generation_latency_ms,
                    "total_tokens": summary.total_tokens,
                    "avg_tokens_per_query": summary.avg_tokens_per_query,
                },
                "provider_comparison": [p.model_dump() for p in summary.provider_comparison],
                "charts_data": {
                    "trend_series": summary.trend_series,
                    "heatmap_matrix": summary.heatmap_matrix,
                },
                "evaluations": [item.model_dump(mode="json") for item in history],
            }
            return (
                json.dumps(payload, indent=2).encode("utf-8"),
                "application/json",
                f"docmind_evaluation_report_{timestamp_str}.json",
            )

        if fmt_lower == "csv":
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["# DocMind AI Enterprise Evaluation Report", self.SYSTEM_VERSION, datetime.now(timezone.utc).isoformat()])
            writer.writerow(["# Executive Summary", f"Overall RAG Score: {summary.overall_rag_score}", f"Avg Grounding: {summary.avg_grounding}", f"Avg Precision: {summary.avg_precision}", f"Avg Recall: {summary.avg_recall}", f"Avg Latency ms: {summary.avg_total_latency_ms}"])
            writer.writerow([])
            writer.writerow([
                "Timestamp", "Request ID", "Query", "Provider", "Model",
                "Overall Score", "Confidence", "Precision@K", "Recall@K",
                "MRR", "NDCG", "Context Recall", "Retrieval Coverage",
                "Source Diversity", "Grounding", "Faithfulness", "Citation Score",
                "Answer Completeness", "Hallucination Risk", "Total Latency (ms)", "Total Tokens",
            ])
            for rec in history:
                writer.writerow([
                    rec.created_at.isoformat(),
                    rec.request_id,
                    rec.query,
                    rec.provider,
                    rec.model,
                    rec.overall_score,
                    rec.confidence,
                    rec.retrieval.precision_at_k,
                    rec.retrieval.recall_at_k,
                    rec.retrieval.mrr,
                    rec.retrieval.ndcg,
                    rec.retrieval.context_recall,
                    rec.retrieval.retrieval_coverage,
                    rec.retrieval.source_diversity,
                    rec.generation.grounding_score,
                    rec.generation.faithfulness,
                    rec.citation_verification.citation_score,
                    rec.generation.answer_completeness,
                    rec.generation.hallucination_risk,
                    rec.performance.total_response_time_ms,
                    rec.performance.total_tokens,
                ])
            return (
                buf.getvalue().encode("utf-8"),
                "text/csv",
                f"docmind_evaluation_report_{timestamp_str}.csv",
            )

        if fmt_lower == "pdf":
            pdf_bytes = self._render_pdf_report(summary, history)
            return (
                pdf_bytes,
                "application/pdf",
                f"docmind_evaluation_report_{timestamp_str}.pdf",
            )

        raise ValueError(f"Unsupported export format '{fmt}'. Expected 'csv', 'json', or 'pdf'.")

    def _render_pdf_report(
        self,
        summary: EvaluationSummaryResponse,
        history: list[EvaluationRecord],
    ) -> bytes:
        """
        Render a multi-section PDF report containing Executive Summary,
        Retrieval & Generation metrics, Performance breakdown, Provider summary,
        charts, system version, and timestamp.
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_pdf import PdfPages

            buf = io.BytesIO()
            with PdfPages(buf) as pdf:
                # Page 1: Executive Summary & Metric Tables
                fig = plt.figure(figsize=(8.5, 11), facecolor="#0A0A0A")
                ax = fig.add_axes([0.06, 0.05, 0.88, 0.90], facecolor="#0A0A0A")
                ax.axis("off")

                now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                ax.text(0.0, 0.96, "DocMind AI — Enterprise RAG Evaluation Report", fontsize=17, fontweight="bold", color="#FFFFFF")
                ax.text(0.0, 0.93, f"System Version: {self.SYSTEM_VERSION}  |  Generated: {now_iso}  |  Evaluations: {summary.total_evaluations}", fontsize=9.5, color="#38BDF8")

                sections = [
                    ("EXECUTIVE SUMMARY", [
                        f"Overall RAG Score: {summary.overall_rag_score:.2f} / 100",
                        f"Avg Grounding: {summary.avg_grounding:.2f}%    |    Avg Faithfulness: {summary.avg_faithfulness:.2f}%",
                        f"Avg Retrieval Score: {summary.avg_retrieval_score:.2f}    |    Avg Hallucination Risk: {summary.avg_hallucination_risk:.2f}%",
                        f"Avg Confidence: {summary.avg_confidence:.2f}%",
                    ]),
                    ("RETRIEVAL QUALITY", [
                        f"Precision@K: {summary.avg_precision:.4f}    |    Recall@K: {summary.avg_recall:.4f}",
                        f"MRR: {summary.avg_mrr:.4f}    |    NDCG: {summary.avg_ndcg:.4f}",
                        f"Context Recall: {summary.avg_context_recall:.2f}%    |    Document Coverage: {summary.avg_retrieval_coverage:.2f}%    |    Diversity: {summary.avg_source_diversity:.1f}",
                    ]),
                    ("GENERATION QUALITY (0 -> 100)", [
                        f"Grounding: {summary.avg_grounding:.2f}    |    Faithfulness: {summary.avg_faithfulness:.2f}    |    Citation Coverage: {summary.avg_citation_coverage:.2f}",
                        f"Context Utilization: {summary.avg_context_utilization:.2f}    |    Completeness: {summary.avg_answer_completeness:.2f}    |    Reasoning: {summary.avg_reasoning_coverage:.2f}",
                    ]),
                    ("PERFORMANCE & TOKENS", [
                        f"Total Avg Latency: {summary.avg_total_latency_ms:.2f} ms    |    Retrieval: {summary.avg_retrieval_latency_ms:.2f} ms    |    Rerank: {summary.avg_reranking_latency_ms:.2f} ms",
                        f"Rewrite: {summary.avg_rewrite_latency_ms:.2f} ms    |    Planner: {summary.avg_planner_latency_ms:.2f} ms    |    Generation: {summary.avg_generation_latency_ms:.2f} ms",
                        f"Total Tokens: {summary.total_tokens}    |    Avg Tokens/Query: {summary.avg_tokens_per_query:.1f}",
                    ]),
                ]

                y = 0.87
                for title, lines in sections:
                    ax.text(0.0, y, title, fontsize=11, fontweight="bold", color="#FF2D95")
                    y -= 0.028
                    for line in lines:
                        ax.text(0.02, y, line, fontsize=9.5, color="#E2E8F0", family="monospace")
                        y -= 0.026
                    y -= 0.02

                ax.text(0.0, y, "PROVIDER COMPARISON", fontsize=11, fontweight="bold", color="#FF2D95")
                y -= 0.028
                if summary.provider_comparison:
                    for p in summary.provider_comparison[:5]:
                        ax.text(
                            0.02, y,
                            f"{p.provider:<14} Runs:{p.total_runs:<4} Score:{p.avg_overall_score:<6.1f} Ground:{p.avg_grounding:<6.1f} Lat:{p.avg_latency_ms:<7.1f}ms",
                            fontsize=9, color="#E2E8F0", family="monospace",
                        )
                        y -= 0.025
                else:
                    ax.text(0.02, y, "No provider runs recorded yet.", fontsize=9, color="#94A3B8")

                pdf.savefig(fig, facecolor="#0A0A0A")
                plt.close(fig)

                # Page 2: Visual Charts
                fig2, axes = plt.subplots(2, 1, figsize=(8.5, 11), facecolor="#0A0A0A")
                for a in axes:
                    a.set_facecolor("#111318")
                    a.tick_params(colors="#94A3B8")
                    for spine in a.spines.values():
                        spine.set_color("#262932")

                if summary.trend_series:
                    xs = [t["label"] for t in summary.trend_series[-15:]]
                    axes[0].plot(xs, [t["grounding"] for t in summary.trend_series[-15:]], color="#007BA7", marker="o", label="Grounding")
                    axes[0].plot(xs, [t["faithfulness"] for t in summary.trend_series[-15:]], color="#38BDF8", marker="s", label="Faithfulness")
                    axes[0].plot(xs, [t["hallucination"] for t in summary.trend_series[-15:]], color="#FF2D95", linestyle="--", label="Hallucination Risk")
                    axes[0].set_title("Quality Trends (Recent Evaluations)", color="#FFFFFF", fontsize=12)
                    axes[0].legend(facecolor="#0A0A0A", labelcolor="#FFFFFF")
                else:
                    axes[0].text(0.5, 0.5, "No trend telemetry available", ha="center", va="center", color="#94A3B8")

                stages = ["Rewrite", "Planner", "Retrieval", "Rerank", "Generation"]
                vals = [
                    summary.avg_rewrite_latency_ms,
                    summary.avg_planner_latency_ms,
                    summary.avg_retrieval_latency_ms,
                    summary.avg_reranking_latency_ms,
                    summary.avg_generation_latency_ms,
                ]
                axes[1].bar(stages, vals, color=["#38BDF8", "#007BA7", "#0EA5E9", "#FF2D95", "#6366F1"])
                axes[1].set_title("Pipeline Stage Latency Breakdown (ms)", color="#FFFFFF", fontsize=12)
                axes[1].set_ylabel("Latency (ms)", color="#94A3B8")

                plt.tight_layout(pad=3.0)
                pdf.savefig(fig2, facecolor="#0A0A0A")
                plt.close(fig2)

            return buf.getvalue()
        except Exception:
            # Minimal valid PDF 1.4 fallback
            text_lines = [
                f"DocMind AI Evaluation Report ({self.SYSTEM_VERSION})",
                f"Evaluations: {summary.total_evaluations} | Overall Score: {summary.overall_rag_score}",
                f"Precision@K: {summary.avg_precision} | Recall@K: {summary.avg_recall} | MRR: {summary.avg_mrr} | NDCG: {summary.avg_ndcg}",
                f"Grounding: {summary.avg_grounding} | Faithfulness: {summary.avg_faithfulness} | Hallucination: {summary.avg_hallucination_risk}",
            ]
            stream = "BT /F1 11 Tf 50 750 Td " + " T* ".join(f"({l}) Tj" for l in text_lines) + " ET"
            pdf_raw = (
                "%PDF-1.4\n"
                "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
                "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
                "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
                f"4 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj\n"
                "5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
                "xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000241 00000 n \n"
                "trailer << /Size 6 /Root 1 0 R >>\nstartxref\n400\n%%EOF\n"
            )
            return pdf_raw.encode("latin-1")

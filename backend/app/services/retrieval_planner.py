"""
Adaptive Hybrid Retrieval Planner for DocMind AI (Sprint 4.4).

Role:
Lightweight pre-retrieval orchestration layer that classifies incoming queries
and selects the optimal retrieval depth, rerank cutoff, memory usage, and
metadata filtering strategy without altering any underlying retrieval math.

Performance Guarantee:
Executes strictly in-memory via pre-compiled regex rules (< 2 ms latency).
Never raises unhandled exceptions; falls back safely to default fact_lookup.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalPlan:
    """
    Structured orchestration plan produced by RetrievalPlanner.
    """

    strategy_name: str
    query_type: str
    recommended_top_k: int
    recommended_rerank_count: int
    needs_memory: bool
    needs_metadata_filter: bool
    reason: str
    decision_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize plan into a JSON-compatible dictionary."""
        return {
            "query_type": self.query_type,
            "strategy": self.strategy_name,
            "strategy_name": self.strategy_name,
            "top_k": self.recommended_top_k,
            "recommended_top_k": self.recommended_top_k,
            "rerank": self.recommended_rerank_count,
            "recommended_rerank_count": self.recommended_rerank_count,
            "memory": self.needs_memory,
            "needs_memory": self.needs_memory,
            "needs_metadata_filter": self.needs_metadata_filter,
            "reason": self.reason,
            "decision_time_ms": self.decision_time_ms,
        }


class RetrievalPlanner:
    """
    Adaptive Hybrid Retrieval Planner.

    Classifies queries into:
      - fact_lookup
      - summary
      - comparison
      - list
      - follow_up
      - code
      - multi_document
    """

    # Pre-compiled patterns for ultra-fast (< 2ms) deterministic classification

    FOLLOW_UP_PRONOUN_RE = re.compile(
        r"\b(it|this|that|these|those|they|them|its|their)\b",
        re.IGNORECASE,
    )
    FOLLOW_UP_STARTER_RE = re.compile(
        r"^(?:and|also|what\s+about|how\s+about|but|so|then|compare\s+(?:with|to))\b",
        re.IGNORECASE,
    )

    CODE_RE = re.compile(
        r"\b(?:show\s+(?:me\s+)?(?:the\s+)?code|write\s+(?:me\s+)?code|source\s+code|code\s+(?:snippet|example)|"
        r"implementation|implement(?:ing)?|python\s+example|javascript\s+example|typescript\s+example|"
        r"pseudocode|syntax|snippet|example\s+code|sample\s+code|how\s+to\s+(?:code|implement))\b|```",
        re.IGNORECASE,
    )

    MULTI_DOC_RE = re.compile(
        r"\b(?:all\s+(?:uploaded\s+)?(?:documents|files|pdfs|docs)|"
        r"across\s+(?:all\s+|the\s+|multiple\s+|every\s+)?(?:documents|files|pdfs|sources|docs)|"
        r"multiple\s+(?:documents|files|pdfs)|"
        r"both\s+(?:documents|files|pdfs|docs)|"
        r"(?:each|every)\s+(?:uploaded\s+)?(?:document|file|pdf)|"
        r"compare\s+(?:the\s+|all\s+)?(?:documents|files|pdfs))\b",
        re.IGNORECASE,
    )

    COMPARISON_RE = re.compile(
        r"\b(?:compare|comparison|difference\s+between|differences\s+between|"
        r"differentiate|versus|vs\.?|contrast|better\s+than|pros\s+and\s+cons)\b",
        re.IGNORECASE,
    )

    SUMMARY_RE = re.compile(
        r"\b(?:summarize|summary|summarise|tldr|tl;dr|key\s+points|key\s+takeaways|"
        r"main\s+points|main\s+ideas|overview|executive\s+summary|high[- ]level\s+summary|"
        r"gist|recap)\b",
        re.IGNORECASE,
    )

    LIST_RE = re.compile(
        r"\b(?:list|enumerate|mention\s+(?:all|every)|name\s+all|give\s+(?:all|me\s+a\s+list)|"
        r"what\s+are\s+(?:all\s+|the\s+)?(?:advantages|disadvantages|limitations|benefits|drawbacks|"
        r"types|kinds|methods|algorithms|datasets|steps|stages|features|applications|use\s+cases|"
        r"challenges|components|examples)|all\s+the|every\s+[a-z]+)\b",
        re.IGNORECASE,
    )

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def _mentions_multiple_files(self, query: str, available_filenames: list[str] | None) -> bool:
        """Check if query explicitly names 2 or more uploaded documents."""
        if not available_filenames or len(available_filenames) < 2:
            return False

        q_lower = query.lower()
        matches = 0
        for fname in available_filenames:
            if not fname:
                continue
            fname_lower = fname.lower().strip()
            stem = fname_lower.rsplit(".", 1)[0] if "." in fname_lower else fname_lower
            if fname_lower in q_lower or (len(stem) >= 3 and re.search(rf"\b{re.escape(stem)}\b", q_lower)):
                matches += 1
                if matches >= 2:
                    return True
        return False

    def plan(
        self,
        query: str,
        original_query: str | None = None,
        is_rewritten: bool = False,
        has_history: bool = False,
        available_filenames: list[str] | None = None,
    ) -> RetrievalPlan:
        """
        Classify query intent and return an adaptive retrieval orchestration plan.
        Guaranteed < 2 ms latency and safe fallback on any error.
        """
        t0 = time.perf_counter()

        try:
            if not self.enabled:
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
                return RetrievalPlan(
                    strategy_name="fact_lookup_search",
                    query_type="fact_lookup",
                    recommended_top_k=5,
                    recommended_rerank_count=3,
                    needs_memory=False,
                    needs_metadata_filter=False,
                    reason="Retrieval planner disabled; using default fact lookup configuration.",
                    decision_time_ms=elapsed_ms,
                )

            raw_check = (original_query or query or "").strip()
            q = (query or "").strip()

            # 1. FOLLOW-UP
            is_follow_up_signal = bool(is_rewritten)
            if not is_follow_up_signal and has_history and raw_check:
                if self.FOLLOW_UP_PRONOUN_RE.search(raw_check) or self.FOLLOW_UP_STARTER_RE.match(raw_check):
                    is_follow_up_signal = True

            if is_follow_up_signal:
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
                return RetrievalPlan(
                    strategy_name="follow_up_search",
                    query_type="follow_up",
                    recommended_top_k=8,
                    recommended_rerank_count=4,
                    needs_memory=True,
                    needs_metadata_filter=False,
                    reason="Follow-up query detected; enabling conversation memory and reusing rewritten query.",
                    decision_time_ms=elapsed_ms,
                )

            # 2. MULTI_DOCUMENT
            if self.MULTI_DOC_RE.search(q) or self._mentions_multiple_files(q, available_filenames):
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
                return RetrievalPlan(
                    strategy_name="multi_document_search",
                    query_type="multi_document",
                    recommended_top_k=15,
                    recommended_rerank_count=7,
                    needs_memory=False,
                    needs_metadata_filter=False,
                    reason="Multi-document reference detected; retrieving balanced evidence from every uploaded document.",
                    decision_time_ms=elapsed_ms,
                )

            # 3. CODE
            if self.CODE_RE.search(q):
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
                return RetrievalPlan(
                    strategy_name="code_search",
                    query_type="code",
                    recommended_top_k=8,
                    recommended_rerank_count=4,
                    needs_memory=False,
                    needs_metadata_filter=True,
                    reason="Code query detected; prioritizing markdown and code-bearing chunks.",
                    decision_time_ms=elapsed_ms,
                )

            # 4. COMPARISON
            if self.COMPARISON_RE.search(q):
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
                return RetrievalPlan(
                    strategy_name="comparison_search",
                    query_type="comparison",
                    recommended_top_k=10,
                    recommended_rerank_count=5,
                    needs_memory=False,
                    needs_metadata_filter=False,
                    reason="Comparison queries benefit from larger candidate pools.",
                    decision_time_ms=elapsed_ms,
                )

            # 5. SUMMARY
            if self.SUMMARY_RE.search(q):
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
                return RetrievalPlan(
                    strategy_name="summary_search",
                    query_type="summary",
                    recommended_top_k=12,
                    recommended_rerank_count=6,
                    needs_memory=False,
                    needs_metadata_filter=False,
                    reason="Summary queries require broader context coverage across sections.",
                    decision_time_ms=elapsed_ms,
                )

            # 6. LIST
            if self.LIST_RE.search(q):
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
                return RetrievalPlan(
                    strategy_name="list_search",
                    query_type="list",
                    recommended_top_k=15,
                    recommended_rerank_count=7,
                    needs_memory=False,
                    needs_metadata_filter=False,
                    reason="List queries require expanded recall to capture all distributed items.",
                    decision_time_ms=elapsed_ms,
                )

            # 7. FACT_LOOKUP (Default)
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
            return RetrievalPlan(
                strategy_name="fact_lookup_search",
                query_type="fact_lookup",
                recommended_top_k=5,
                recommended_rerank_count=3,
                needs_memory=False,
                needs_metadata_filter=False,
                reason="Fact lookup query uses focused top-k precision and tight reranking.",
                decision_time_ms=elapsed_ms,
            )

        except Exception as exc:
            logger.warning("RetrievalPlanner encountered an error (%s); falling back to fact_lookup.", exc)
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
            return RetrievalPlan(
                strategy_name="fact_lookup_search",
                query_type="fact_lookup",
                recommended_top_k=5,
                recommended_rerank_count=3,
                needs_memory=False,
                needs_metadata_filter=False,
                reason="Fallback to default fact lookup due to planner error.",
                decision_time_ms=elapsed_ms,
            )


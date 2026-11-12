"""
QueryRewriter: High-performance pre-retrieval query optimization for DocMind AI.

Objectives & Rules:
- Conservative enhancement: NEVER invent new information, NEVER answer the question.
- Disambiguates pronouns (it, this, that, these, those, they, them) and follow-up fragments.
- Resolves context from recent conversation turns.
- Maximum latency: < 50 ms (pure string/heuristic parsing executes in < 1 ms).
- Graceful degradation: any failure returns original query without propagating exceptions.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class QueryRewriteResult:
    """Telemetry payload for query rewrite execution."""

    original_query: str
    rewritten_query: str
    rewrite_time_ms: float
    status: str  # "rewritten" | "skipped" | "disabled" | "failed"
    is_rewritten: bool


class QueryRewriter:
    """
    Isolated Query Rewrite Service.
    Transforms incomplete or pronoun-heavy user questions into clear retrieval queries.
    """

    # Target pronouns that trigger pronoun resolution
    PRONOUN_PATTERN = re.compile(
        r"\b(it|this|that|these|those|they|them|its|their)\b",
        re.IGNORECASE,
    )

    # Question prefix removers to isolate core topic from historical query
    QUESTION_STARTERS = re.compile(
        r"^(?:what\s+(?:is|are|was|were|do\s+you\s+mean\s+by)|tell\s+me\s+about|explain|describe|define|overview\s+of|how\s+(?:do|does|did|is|are)|can\s+you\s+explain|what\s+about|how\s+about)\s+",
        re.IGNORECASE,
    )

    # Leading articles
    LEADING_ARTICLES = re.compile(r"^(?:the|a|an)\s+", re.IGNORECASE)

    # Trailing polite / modifier phrases
    TRAILING_MODIFIERS = re.compile(
        r"\s+(?:simply|in\s+detail|briefly|please|for\s+me|works?)$",
        re.IGNORECASE,
    )

    # Standard conversational follow-up triggers
    FOLLOW_UP_STARTERS = re.compile(
        r"^(?:and|also|what\s+about|how\s+about|but|so|then)\b",
        re.IGNORECASE,
    )

    # Domain aspect keywords
    ASPECT_KEYWORDS = {
        "advantages",
        "disadvantages",
        "benefits",
        "drawbacks",
        "limitations",
        "applications",
        "use cases",
        "features",
        "pros and cons",
        "challenges",
        "characteristics",
        "components",
        "architecture",
    }

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def extract_context(self, history: list[Any]) -> str | None:
        """
        Extract the salient entity or topic from recent conversation history.
        Inspects turns from newest to oldest.
        """
        if not history:
            return None

        # Inspect chronologically newest turns first
        for turn in reversed(history):
            raw_text = ""
            if isinstance(turn, str):
                raw_text = turn.strip()
            elif hasattr(turn, "query"):
                raw_text = str(turn.query or "").strip()
            elif isinstance(turn, dict):
                raw_text = str(turn.get("query") or turn.get("content") or "").strip()

            if not raw_text:
                continue

            # Strip trailing question marks and punctuation
            cleaned = raw_text.rstrip("?!. ")

            # Strip question starters
            cleaned = self.QUESTION_STARTERS.sub("", cleaned).strip()

            # Strip leading articles
            cleaned = self.LEADING_ARTICLES.sub("", cleaned).strip()

            # Strip trailing modifiers
            cleaned = self.TRAILING_MODIFIERS.sub("", cleaned).strip()

            # Strip trailing punctuation again
            cleaned = cleaned.rstrip("?!. ").strip()

            if cleaned and len(cleaned) >= 2:
                lower_c = cleaned.lower()
                # Skip if extracted fragment is itself a pronoun or generic aspect
                if lower_c in {"it", "this", "that", "these", "those", "they", "them", "its", "their"} or lower_c in self.ASPECT_KEYWORDS:
                    continue
                return cleaned

        return None

    def should_accept(self, query: str, context: str | None = None) -> bool:
        """
        Conservative gate: determines whether the query requires rewriting.
        Returns False if no historical context exists or query is already self-contained.
        """
        if not context or not context.strip():
            return False

        q = query.strip()
        if not q:
            return False

        # 1. Contains pronouns (it, this, that, these, those, they, them, its, their)
        if self.PRONOUN_PATTERN.search(q):
            return True

        # 2. Starts with follow-up connector (e.g. "And disadvantages?", "What about unsupervised?")
        if self.FOLLOW_UP_STARTERS.match(q):
            return True

        # 3. Missing subject comparative (e.g. "Compare with SVM", "Differences with ...")
        if re.match(r"^(?:compare|difference|differences|versus|vs\.?)\b", q, re.IGNORECASE):
            return True

        # 4. Short ambiguous single-aspect query (e.g. "Advantages?", "Limitations?")
        q_clean = q.rstrip("?!. ").strip().lower()
        if q_clean in self.ASPECT_KEYWORDS:
            return True

        # 5. Short phrase (< 4 words) lacking a main subject
        words = q_clean.split()
        if len(words) <= 3 and re.match(r"^(?:why|how|what|explain|pros|cons)\b", q_clean, re.IGNORECASE):
            return True

        return False

    def rewrite(self, query: str, history: list[Any] | None = None) -> QueryRewriteResult:
        """
        Disambiguate and optimize the retrieval query using conversation context.
        Guarantees < 50 ms latency and never propagates exceptions.
        """
        clean_query = query.strip()
        if not self.enabled:
            return QueryRewriteResult(
                original_query=clean_query,
                rewritten_query=clean_query,
                rewrite_time_ms=0.0,
                status="disabled",
                is_rewritten=False,
            )

        t0 = time.perf_counter()

        try:
            # 1. Extract context from history
            context = self.extract_context(history or [])

            # 2. Gatekeeper: only rewrite if query qualifies
            if not self.should_accept(clean_query, context):
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
                return QueryRewriteResult(
                    original_query=clean_query,
                    rewritten_query=clean_query,
                    rewrite_time_ms=elapsed_ms,
                    status="skipped",
                    is_rewritten=False,
                )

            assert context is not None  # Guaranteed by should_accept

            q_stripped = clean_query.rstrip("?!. ").strip()
            q_lower = q_stripped.lower()
            rewritten: str | None = None

            # -----------------------------------------------------------
            # Pattern A: Comparative with Missing First Subject
            # Example: "Compare with SVM" -> "Compare Random Forest with SVM."
            # -----------------------------------------------------------
            m_comp = re.match(
                r"^(?:can\s+you\s+)?compare(?:\s+it)?\s+(?:with|to)\s+(.+)$",
                q_stripped,
                re.IGNORECASE,
            )
            if m_comp:
                target = m_comp.group(1).strip()
                rewritten = f"Compare {context} with {target}."

            # Example: "Differences with SVM" -> "What are the differences between Random Forest and SVM?"
            if not rewritten:
                m_diff = re.match(
                    r"^(?:what\s+are\s+the\s+)?(?:difference|differences)\s+(?:between|with)\s+(.+)$",
                    q_stripped,
                    re.IGNORECASE,
                )
                if m_diff:
                    target = m_diff.group(1).strip()
                    rewritten = f"What are the differences between {context} and {target}?"

            # -----------------------------------------------------------
            # Pattern B: Aspect-only question
            # Examples:
            #   "Advantages?" -> "What are the advantages of Decision Trees?"
            #   "And disadvantages?" -> "What are the disadvantages of Neural Networks?"
            # -----------------------------------------------------------
            if not rewritten:
                m_aspect = re.match(
                    r"^(?:(?:and|also|what\s+about|how\s+about)\s+)?(advantages|disadvantages|benefits|drawbacks|limitations|applications|use\s+cases|features|pros\s+and\s+cons|challenges)$",
                    q_lower,
                )
                if m_aspect:
                    aspect = m_aspect.group(1).strip()
                    rewritten = f"What are the {aspect} of {context}?"

            # -----------------------------------------------------------
            # Pattern C: Contrastive / Parallel Follow-up
            # Example:
            #   Input: "And unsupervised?"
            #   History: "What about supervised learning?" (context = "supervised learning")
            #   Output: "What is unsupervised learning?"
            # -----------------------------------------------------------
            if not rewritten:
                m_para = re.match(
                    r"^(?:and|what\s+about|how\s+about)\s+([a-zA-Z0-9_\-\s]+)$",
                    q_stripped,
                    re.IGNORECASE,
                )
                if m_para:
                    candidate = m_para.group(1).strip()
                    # Check if context ends with a category/head noun (e.g. "supervised learning" -> "learning")
                    context_words = context.split()
                    if len(context_words) > 1:
                        head_noun = context_words[-1]
                        if not candidate.lower().endswith(head_noun.lower()):
                            rewritten = f"What is {candidate} {head_noun}?"
                        else:
                            rewritten = f"What is {candidate}?"
                    else:
                        rewritten = f"What is {candidate}?"

            # -----------------------------------------------------------
            # Pattern D: Pronoun Replacement
            # Examples:
            #   "Explain it" -> "Explain Perceptron."
            #   "Explain it simply" -> "Explain Perceptron simply."
            #   "How does it work?" -> "How does Perceptron work?"
            #   "What is its architecture?" -> "What is Perceptron's architecture?"
            # -----------------------------------------------------------
            if not rewritten and self.PRONOUN_PATTERN.search(clean_query):
                res_str = clean_query
                # Handle possessives first
                res_str = re.sub(r"\b(its|their)\b", f"{context}'s", res_str, flags=re.IGNORECASE)
                # Handle standard pronouns
                res_str = re.sub(
                    r"\b(it|this|that|these|those|they|them)\b",
                    context,
                    res_str,
                    flags=re.IGNORECASE,
                )

                # Format punctuation: if original didn't end with ?, ensure appropriate . or ?
                if not res_str.endswith(("?", ".", "!")):
                    if re.match(r"^(?:what|how|why|when|where|who|is|are|can|could|does|do)\b", res_str, re.I):
                        res_str += "?"
                    else:
                        res_str += "."

                rewritten = res_str

            # -----------------------------------------------------------
            # Final Clean-Up
            # -----------------------------------------------------------
            if rewritten and rewritten.strip() and rewritten.strip() != clean_query:
                # Capitalize first letter
                final_rewritten = rewritten[0].upper() + rewritten[1:]
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
                return QueryRewriteResult(
                    original_query=clean_query,
                    rewritten_query=final_rewritten,
                    rewrite_time_ms=elapsed_ms,
                    status="rewritten",
                    is_rewritten=True,
                )

            # Fallback if no specific transformation applied
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            return QueryRewriteResult(
                original_query=clean_query,
                rewritten_query=clean_query,
                rewrite_time_ms=elapsed_ms,
                status="skipped",
                is_rewritten=False,
            )

        except Exception as exc:
            logger.warning(
                "Query rewrite encountered an unexpected error: %s; falling back to original query.",
                exc,
            )
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            return QueryRewriteResult(
                original_query=clean_query,
                rewritten_query=clean_query,
                rewrite_time_ms=elapsed_ms,
                status="failed",
                is_rewritten=False,
            )

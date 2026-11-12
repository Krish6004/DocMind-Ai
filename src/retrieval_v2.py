"""
Retrieval V2 enhancements for DocMind AI.

Provides explainability, confidence scoring, chunk highlighting,
metadata filtering, metrics tracking, and query history management
without modifying any underlying retrieval or reranking algorithms.
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.logger import get_logger
from src.utils import source_basename

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# 1. Retrieval Confidence Computation
# ---------------------------------------------------------------------------


def sigmoid(x: float) -> float:
    """
    Numerically stable logistic sigmoid function.

    Maps unbounded cross-encoder logits into the probability interval (0, 1).
    """
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = math.exp(x)
        return z / (1.0 + z)


def compute_retrieval_confidence(
    chunks: list[dict[str, Any]],
    rerank_weight: float = 0.70,
    similarity_weight: float = 0.30,
) -> dict[str, Any]:
    """
    Calculate an explainable confidence score from normalized retrieval & reranker scores.

    Formulation:
      1. Reranker Score: The cross-encoder raw logit s_rerank is converted into
         a calibrated probability P_rerank via logistic sigmoid:
             P_rerank = 1 / (1 + exp(-s_rerank))
      2. Dense Similarity Score: Cosine similarity s_sim in [-1, 1] is clipped
         to [0, 1]:
             P_sim = max(0.0, min(1.0, s_sim))
         If similarity_score is absent, RRF normalized score is used.
      3. Composite Confidence:
             C = w_rerank * P_rerank + w_sim * P_sim
      4. Tiers:
             C >= 0.70  -> High Confidence
             0.40 <= C < 0.70 -> Medium Confidence
             C < 0.40   -> Low Confidence

    Args:
        chunks: List of retrieved/reranked chunk dictionaries.
        rerank_weight: Weight assigned to cross-encoder score (default: 0.70).
        similarity_weight: Weight assigned to dense similarity score (default: 0.30).

    Returns:
        Structured confidence dictionary with score, percentage, tier level,
        color code, detailed explanation, and component metrics.
    """
    if not chunks:
        return {
            "score": 0.0,
            "percentage": 0.0,
            "level": "Low",
            "color": "#ef4444",
            "explanation": "No relevant document chunks were retrieved for this query.",
            "details": {
                "top_rerank_score": None,
                "normalized_rerank_score": 0.0,
                "top_similarity_score": None,
                "normalized_similarity_score": 0.0,
                "rerank_weight": rerank_weight,
                "similarity_weight": similarity_weight,
            },
        }

    top_chunk = chunks[0]
    meta = top_chunk.get("metadata", {})
    filename = source_basename(meta)

    # 1. Evaluate reranker score
    top_rerank = top_chunk.get("rerank_score")
    if top_rerank is not None:
        norm_rerank = sigmoid(float(top_rerank))
        has_rerank = True
    else:
        norm_rerank = 0.0
        has_rerank = False

    # 2. Evaluate similarity score
    top_sim = top_chunk.get("similarity_score")
    if top_sim is not None:
        norm_sim = max(0.0, min(1.0, float(top_sim)))
        has_sim = True
    else:
        # Fall back to RRF score if present
        raw_score = top_chunk.get("score")
        if raw_score is not None:
            # Theoretical max RRF for top-1 in 2 lists (k=60) is ~ 2/61 = 0.03278688
            max_rrf = 2.0 / 61.0
            norm_sim = max(0.0, min(1.0, float(raw_score) / max_rrf))
            has_sim = True
            top_sim = raw_score
        else:
            norm_sim = 0.0
            has_sim = False

    # 3. Fuse scores based on available components
    if has_rerank and has_sim:
        score = rerank_weight * norm_rerank + similarity_weight * norm_sim
    elif has_rerank:
        score = norm_rerank
    elif has_sim:
        score = norm_sim
    else:
        score = 0.50

    score = max(0.0, min(1.0, float(score)))
    percentage = round(score * 100, 1)

    # 4. Classify confidence tiers
    if score >= 0.70:
        level = "High"
        color = "#22c55e"
    elif score >= 0.40:
        level = "Medium"
        color = "#eab308"
    else:
        level = "Low"
        color = "#ef4444"

    # 5. Formulate transparent explanation
    rerank_part = (
        f"Cross-Encoder logit ({top_rerank:+.2f} → {norm_rerank * 100:.1f}%, weight {int(rerank_weight * 100)}%)"
        if has_rerank
        else "no reranker score"
    )
    sim_part = (
        f"Dense Similarity ({top_sim:.3f} → {norm_sim * 100:.1f}%, weight {int(similarity_weight * 100)}%)"
        if has_sim
        else "no similarity score"
    )

    explanation = (
        f"Confidence is {percentage}% ({level}). Evaluated on top chunk from '{filename}': "
        f"{rerank_part} and {sim_part} combined indicate "
        f"{'high factual grounding and strong semantic alignment' if level == 'High' else 'moderate relevance; check sources carefully' if level == 'Medium' else 'weak context alignment; caution advised'}."
    )

    return {
        "score": round(score, 4),
        "percentage": percentage,
        "level": level,
        "color": color,
        "explanation": explanation,
        "details": {
            "top_rerank_score": round(float(top_rerank), 4) if top_rerank is not None else None,
            "normalized_rerank_score": round(norm_rerank, 4),
            "top_similarity_score": round(float(top_sim), 4) if top_sim is not None else None,
            "normalized_similarity_score": round(norm_sim, 4),
            "rerank_weight": rerank_weight,
            "similarity_weight": similarity_weight,
        },
    }


# ---------------------------------------------------------------------------
# 2. Metadata Filtering
# ---------------------------------------------------------------------------


def matches_metadata_filter(
    metadata: dict[str, Any] | None,
    filter_dict: dict[str, Any] | None,
) -> bool:
    """
    Check if a document chunk's metadata satisfies the given filter criteria.

    Supported filter fields:
      - filename: matches metadata.get("filename") or source path basename
      - file_type / document_type: matches metadata.get("file_type") (pdf, docx, txt, md)
      - uploaded_date / date: matches YYYY-MM-DD prefix of upload_timestamp
      - date_from / date_to: date range comparison on upload_timestamp

    Wildcards: None, "", "All", "All Documents", "All Types", "All Dates" bypass the filter.
    """
    if not filter_dict:
        return True

    meta = metadata or {}

    # 1. Filename filter
    target_filename = filter_dict.get("filename")
    if target_filename and target_filename not in ("All", "All Documents", ""):
        chunk_file = meta.get("filename", "")
        chunk_source = meta.get("source", "")
        target_norm = target_filename.lower().strip()
        if (
            chunk_file.lower().strip() != target_norm
            and Path(chunk_file).name.lower().strip() != target_norm
            and Path(chunk_source).name.lower().strip() != target_norm
        ):
            return False

    # 2. File type filter
    target_type = filter_dict.get("file_type") or filter_dict.get("document_type")
    if target_type and target_type not in ("All", "All Types", ""):
        chunk_type = meta.get("file_type", "").lower().lstrip(".")
        target_norm = target_type.lower().lstrip(".")
        if chunk_type != target_norm:
            return False

    # 3. Exact date filter
    target_date = filter_dict.get("uploaded_date") or filter_dict.get("date")
    if target_date and target_date not in ("All", "All Dates", ""):
        ts = str(meta.get("upload_timestamp", ""))
        target_str = str(target_date).strip()
        if not ts.startswith(target_str):
            return False

    # 4. Date range filter
    date_from = filter_dict.get("date_from")
    if date_from:
        ts = str(meta.get("upload_timestamp", ""))[:10]
        if ts and ts < str(date_from).strip():
            return False

    date_to = filter_dict.get("date_to")
    if date_to:
        ts = str(meta.get("upload_timestamp", ""))[:10]
        if ts and ts > str(date_to).strip():
            return False

    # 5. User isolation filter (Sprint 7.0)
    target_user_id = filter_dict.get("user_id")
    if target_user_id and target_user_id not in ("All", "default", ""):
        chunk_user = meta.get("user_id")
        if chunk_user and chunk_user != target_user_id:
            return False

    return True


def filter_chunks_by_metadata(
    chunks: list[dict[str, Any]],
    filter_dict: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """
    Filter a list of document chunks according to metadata filter criteria.
    """
    if not filter_dict:
        return chunks
    return [c for c in chunks if matches_metadata_filter(c.get("metadata", {}), filter_dict)]


# ---------------------------------------------------------------------------
# 3. Chunk Highlighting & Citation Attribution
# ---------------------------------------------------------------------------


def identify_used_chunks(
    answer: str,
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Identify and annotate which chunks were directly cited or used for generating the answer.

    Examines:
      1. Explicit [Source N] or Source N tags cited in the LLM answer.
      2. If no explicit tags exist, identifies the primary chunk with highest text overlap.

    Returns a new list of chunk dicts enriched with:
      - is_used: bool
      - citation_number: int | None
      - highlighted_html: str (with preserved formatting)
    """
    if not chunks:
        return []

    # Detect explicit citations: [Source 1], [Source 2], Source 1, etc.
    pattern = r"(?:\[Source\s*(\d+)\]|\bSource\s*(\d+)\b)"
    matches = re.findall(pattern, answer, re.IGNORECASE)
    cited_nums: set[int] = set()
    for m in matches:
        for group in m:
            if group and group.isdigit():
                cited_nums.add(int(group))

    has_explicit_citations = len(cited_nums) > 0

    # Fallback overlap detection if no explicit citation present
    best_overlap_idx = 0
    if not has_explicit_citations:
        best_overlap_score = -1.0
        # Tokenize answer into alphanumeric words
        answer_words = set(re.findall(r"\w{4,}", answer.lower()))
        for idx, chunk in enumerate(chunks):
            chunk_words = set(re.findall(r"\w{4,}", chunk.get("text", "").lower()))
            overlap = len(answer_words & chunk_words)
            if overlap > best_overlap_score:
                best_overlap_score = overlap
                best_overlap_idx = idx

    enriched: list[dict[str, Any]] = []
    for i, chunk in enumerate(chunks, start=1):
        if has_explicit_citations:
            is_used = i in cited_nums
            citation_num = i if is_used else None
        else:
            is_used = (i - 1) == best_overlap_idx
            citation_num = i if is_used else None

        text = chunk.get("text", "")
        highlighted = highlight_chunk_html(text, answer) if is_used else text

        enriched.append(
            {
                **chunk,
                "is_used": is_used,
                "citation_number": citation_num,
                "highlighted_html": highlighted,
            }
        )

    return enriched


def highlight_chunk_html(chunk_text: str, answer: str) -> str:
    """
    Highlight salient matching phrases in chunk_text used by the answer,
    strictly preserving all original whitespace, newlines, indentation, and formatting.

    Identifies matching clauses and significant multi-word phrase patterns from the answer,
    wrapping spans in <mark class="docmind-highlight">...</mark>.
    """
    if not chunk_text or not answer:
        return chunk_text

    spans: list[tuple[int, int]] = []
    common_stopwords = {
        "the", "and", "for", "with", "that", "this", "from", "are",
        "was", "were", "has", "have", "had", "include", "includes",
        "into", "over", "about", "such", "then", "them", "these",
    }

    # 1. Search for full clauses/sentences from answer
    clauses = re.split(r"[.\n?!;]+", answer)

    for clause in clauses:
        clause_clean = clause.strip()
        if len(clause_clean) >= 15 and clause_clean.lower() in chunk_text.lower():
            pos = chunk_text.lower().find(clause_clean.lower())
            while pos != -1:
                spans.append((pos, pos + len(clause_clean)))
                pos = chunk_text.lower().find(clause_clean.lower(), pos + 1)
            continue

        # 2. Extract salient words (length >= 3)
        words = re.findall(r"[A-Za-z0-9_-]{3,}", clause)
        if len(words) < 2:
            continue

        # Try sliding n-grams of size 5 down to 2
        for n in range(min(len(words), 5), 1, -1):
            for i in range(len(words) - n + 1):
                ngram = words[i : i + n]
                # Must have at least one non-stopword of length >= 4
                if not any(w.lower() not in common_stopwords and len(w) >= 4 for w in ngram):
                    continue

                pattern_str = r"\b" + r"[\s\W]+".join(re.escape(w) for w in ngram) + r"\b"
                try:
                    for match in re.finditer(pattern_str, chunk_text, re.IGNORECASE):
                        spans.append((match.start(), match.end()))
                except re.error:
                    continue

    if not spans:
        return chunk_text

    # Merge overlapping and adjacent spans
    spans.sort(key=lambda x: x[0])
    merged_spans: list[tuple[int, int]] = []
    for start, end in spans:
        if not merged_spans:
            merged_spans.append((start, end))
        else:
            prev_start, prev_end = merged_spans[-1]
            if start <= prev_end:
                merged_spans[-1] = (prev_start, max(prev_end, end))
            else:
                merged_spans.append((start, end))

    # Construct HTML highlighting while preserving exact characters
    out: list[str] = []
    cursor = 0
    mark_style = (
        'style="background: rgba(245, 158, 11, 0.28); color: inherit; '
        'padding: 1px 4px; border-radius: 4px; font-weight: 600;"'
    )

    for start, end in merged_spans:
        if start > cursor:
            out.append(chunk_text[cursor:start])
        out.append(f'<mark class="docmind-highlight" {mark_style}>')
        out.append(chunk_text[start:end])
        out.append("</mark>")
        cursor = end

    if cursor < len(chunk_text):
        out.append(chunk_text[cursor:])

    return "".join(out)


# ---------------------------------------------------------------------------
# 4. Retrieval Metrics Dataclass
# ---------------------------------------------------------------------------


@dataclass
class RetrievalMetrics:
    """
    Performance and operational telemetry for a RAG retrieval & generation query.
    """

    retrieval_latency_ms: float
    reranking_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float
    retrieved_chunk_count: int
    reranked_chunk_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 5. Recent Queries Manager
# ---------------------------------------------------------------------------


def add_recent_query(
    recent_list: list[str],
    query: str,
    max_items: int = 10,
) -> list[str]:
    """
    Append a query to the recent queries list, moving it to front and deduplicating.
    Caps history at max_items (default 10).
    """
    q = query.strip()
    if not q:
        return list(recent_list)

    # Filter out existing occurrences (case-insensitive deduplication)
    updated = [item for item in recent_list if item.strip().lower() != q.lower()]
    updated.insert(0, q)
    return updated[:max_items]

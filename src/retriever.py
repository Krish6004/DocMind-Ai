"""
Hybrid retriever for DocMind AI combining dense (semantic) + sparse (BM25)
retrieval using Reciprocal Rank Fusion (RRF).

Why hybrid?
  - Dense retrieval excels at semantic similarity ("furry pet" → "cat")
  - Sparse retrieval excels at exact keyword matching ("PyTorch 2.1 release notes")
  - RRF combines both rankings without requiring score calibration between models

RRF formula:
    RRF_score(d) = Σ_{list L}  1 / (k + rank_L(d))

    where rank is 1-based, k=60 is a smoothing constant (standard default).
    Documents not in a given list contribute 0 for that list.
    Higher score = more relevant.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.logger import get_logger

if TYPE_CHECKING:
    from src.bm25 import BM25
    from src.embeddings import EmbeddingModel
    from src.vectorstore import VectorStore

logger = get_logger(__name__)


class HybridRetriever:
    """
    Retrieves documents by fusing dense and sparse rankings via RRF.

    Args:
        vectorstore: Populated VectorStore instance.
        bm25:        Fitted BM25 instance.
        embedder:    EmbeddingModel for query encoding.
        rrf_k:       RRF smoothing constant (default 60).
    """

    def __init__(
        self,
        vectorstore: VectorStore,
        bm25: BM25,
        embedder: EmbeddingModel,
        rrf_k: int = 60,
    ) -> None:
        self.vectorstore = vectorstore
        self.bm25 = bm25
        self.embedder = embedder
        self.rrf_k = rrf_k
        logger.debug("Initialized %r", self)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        dense_top_k: int | None = None,
        sparse_top_k: int | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve the top_k most relevant documents for a query.

        Over-fetches from each retriever (3× top_k, min 20) to give RRF
        enough candidates to fuse before final truncation to top_k.

        Args:
            query:           Raw query string.
            top_k:           Number of final results to return.
            dense_top_k:     Candidates from dense retriever (default: 3× top_k, ≥20).
            sparse_top_k:    Candidates from sparse retriever (default: 3× top_k, ≥20).
            metadata_filter: Optional metadata filtering criteria (e.g. filename, file_type, date).

        Returns:
            List of dicts with keys: text, metadata, score (RRF), similarity_score, index.
        """
        from src.retrieval_v2 import matches_metadata_filter

        candidate_k = max(top_k * 3, 20)
        if dense_top_k is None:
            dense_top_k = candidate_k
        if sparse_top_k is None:
            sparse_top_k = candidate_k

        # --- Dense retrieval ---
        query_vec = self.embedder.embed_query(query)
        dense_results = self.vectorstore.search(query_vec, top_k=dense_top_k)

        # --- Sparse retrieval ---
        sparse_results = self.bm25.get_top_n(query, n=sparse_top_k)

        index_to_dense: dict[int, dict] = {r["index"]: r for r in dense_results}

        # --- Metadata filtering (if active) ---
        if metadata_filter:
            dense_results = [
                r for r in dense_results if matches_metadata_filter(r.get("metadata", {}), metadata_filter)
            ]

            filtered_sparse = []
            for r in sparse_results:
                idx = r["index"]
                if idx in index_to_dense:
                    meta = index_to_dense[idx].get("metadata", {})
                elif hasattr(self.vectorstore, "get_by_index"):
                    try:
                        meta = self.vectorstore.get_by_index(idx).get("metadata", {})
                    except Exception:
                        meta = {}
                elif hasattr(self.vectorstore, "_metadata") and idx < len(self.vectorstore._metadata):
                    meta = self.vectorstore._metadata[idx]
                else:
                    meta = {}

                if matches_metadata_filter(meta, metadata_filter):
                    filtered_sparse.append(r)
            sparse_results = filtered_sparse

        # --- Fuse with RRF ---
        fused = self._reciprocal_rank_fusion([dense_results, sparse_results], self.rrf_k)

        # --- Enrich sparse-only hits with vectorstore text/metadata ---
        enriched: list[dict] = []
        for item in fused[:top_k]:
            idx = item["index"]
            if idx in index_to_dense:
                base = index_to_dense[idx]
                sim_score = base.get("score")
            else:
                # Sparse-only hit: pull text + metadata from vectorstore
                base = self.vectorstore.get_by_index(idx)
                sim_score = None
            enriched.append(
                {
                    "text": base["text"],
                    "metadata": base.get("metadata", {}),
                    "score": item["rrf_score"],
                    "similarity_score": sim_score,
                    "index": idx,
                }
            )

        return enriched

    # ------------------------------------------------------------------
    # Reciprocal Rank Fusion
    # ------------------------------------------------------------------

    def _reciprocal_rank_fusion(
        self,
        ranked_lists: list[list[dict]],
        rrf_k: int,
    ) -> list[dict]:
        """
        Fuse multiple ranked lists using RRF.

        Each list must contain dicts with an "index" key (document id).

        Returns a list sorted by descending RRF score, with added key
        "rrf_score".
        """
        scores: dict[int, float] = {}

        for ranked_list in ranked_lists:
            for rank_0based, item in enumerate(ranked_list):
                doc_idx = item["index"]
                rank_1based = rank_0based + 1
                scores[doc_idx] = scores.get(doc_idx, 0.0) + 1.0 / (rrf_k + rank_1based)

        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [{"index": idx, "rrf_score": score} for idx, score in sorted_items]

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"HybridRetriever(rrf_k={self.rrf_k}, store_size={len(self.vectorstore)})"

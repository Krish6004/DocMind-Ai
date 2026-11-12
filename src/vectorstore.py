"""
Custom vector store backed by NumPy arrays for DocMind AI.

Stores L2-normalized float32 embeddings alongside document text and metadata.
Similarity search is exact cosine similarity via dot-product on pre-normalized
vectors.

Save format:
  {path}.npz  — NumPy archive with key "embeddings"
  {path}.json — JSON array of {"document": str, "metadata": dict} objects
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from src.logger import get_logger
from src.utils import top_k_indices

logger = get_logger(__name__)


class VectorStore:
    """
    Exact cosine similarity vector store.

    Usage::

        store = VectorStore()
        store.add(embeddings, documents, metadata_list)
        results = store.search(query_embedding, top_k=5)
        store.save("data/store")
        store.load("data/store")
    """

    def __init__(self) -> None:
        # Embeddings matrix: shape (N, D), float32, L2-normalized
        self._embeddings: np.ndarray | None = None
        self._documents: list[str] = []
        self._metadata: list[dict[str, Any]] = []


    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def add(
        self,
        embeddings: np.ndarray,
        documents: list[str],
        metadata: list[dict[str, Any]],
    ) -> None:
        """
        Add a batch of embeddings and their associated documents.

        Args:
            embeddings: shape (N, D), expected to be L2-normalized float32.
            documents:  list of N document strings.
            metadata:   list of N metadata dicts (arbitrary keys).
        """
        if len(embeddings) != len(documents) or len(embeddings) != len(metadata):
            raise ValueError("embeddings, documents, and metadata must all have the same length")
        if len(embeddings) == 0:
            return

        embeddings = np.array(embeddings, dtype=np.float32)

        if self._embeddings is None:
            self._embeddings = embeddings
        else:
            self._embeddings = np.concatenate([self._embeddings, embeddings], axis=0)

        self._documents.extend(documents)
        self._metadata.extend(metadata)
        logger.debug("Added %d documents to VectorStore (total: %d)", len(documents), len(self._documents))


    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Return the top_k most similar documents by cosine similarity.

        Since all stored embeddings and the query are L2-normalized,
        cosine similarity == dot product.

        Returns a list of dicts with keys:
            text     – document string
            metadata – metadata dict
            score    – cosine similarity in [-1, 1]
            index    – position in the internal store
        """
        if self._embeddings is None or len(self._documents) == 0:
            return []

        query = np.array(query_embedding, dtype=np.float32).flatten()

        # Cosine similarity as dot product (vectors are pre-normalized)
        scores: np.ndarray = self._embeddings @ query  # shape (N,)

        k = min(top_k, len(self._documents))
        top_idx = top_k_indices(scores, k)

        results: list[dict[str, Any]] = []
        for idx in top_idx:
            idx_int = int(idx)
            results.append(
                {
                    "text": self._documents[idx_int],
                    "metadata": self._metadata[idx_int],
                    "score": float(scores[idx_int]),
                    "index": idx_int,
                }
            )
        return results

    def get_by_index(self, idx: int) -> dict[str, Any]:
        """
        Return the document text and metadata at a given index.

        Args:
            idx: Position in the internal store.

        Returns:
            {"text": str, "metadata": dict, "index": int}
        """
        return {
            "text": self._documents[idx],
            "metadata": self._metadata[idx],
            "index": idx,
        }

    # ------------------------------------------------------------------
    # Granular Deletion & Dynamic Index Modification
    # ------------------------------------------------------------------

    def delete_by_filename(self, filename: str) -> int:
        """
        Delete all document chunks matching the given filename.

        Matches against:
          - meta.get("filename") == filename
          - Path(meta.get("source", "")).name == filename
          - meta.get("source") == filename

        Performs instant row-slicing on the internal NumPy embeddings matrix
        and metadata lists without re-embedding any remaining documents.

        Args:
            filename: Name or source path of the document to remove.

        Returns:
            Number of chunks removed.
        """
        if not self._documents:
            return 0

        indices_to_keep: list[int] = []
        deleted_count = 0

        for i, meta in enumerate(self._metadata):
            fname = meta.get("filename")
            source = meta.get("source", "")
            source_name = Path(source).name if source else ""
            if fname == filename or source == filename or source_name == filename:
                deleted_count += 1
            else:
                indices_to_keep.append(i)

        if deleted_count == 0:
            return 0

        if not indices_to_keep:
            self._embeddings = None
            self._documents = []
            self._metadata = []
        else:
            keep_arr = np.array(indices_to_keep, dtype=np.intp)
            if self._embeddings is not None:
                self._embeddings = self._embeddings[keep_arr]
            self._documents = [self._documents[i] for i in indices_to_keep]
            self._metadata = [self._metadata[i] for i in indices_to_keep]

        logger.debug(
            "Deleted %d chunks for filename '%s' from VectorStore (remaining: %d)",
            deleted_count,
            filename,
            len(self._documents),
        )
        return deleted_count

    def delete_by_metadata(self, key: str, value: Any) -> int:
        """
        Delete all chunks where chunk metadata matches key == value.

        Args:
            key: Metadata key name.
            value: Value to match for deletion.

        Returns:
            Number of chunks removed.
        """
        if not self._documents:
            return 0

        indices_to_keep: list[int] = []
        deleted_count = 0

        for i, meta in enumerate(self._metadata):
            if meta.get(key) == value:
                deleted_count += 1
            else:
                indices_to_keep.append(i)

        if deleted_count == 0:
            return 0

        if not indices_to_keep:
            self._embeddings = None
            self._documents = []
            self._metadata = []
        else:
            keep_arr = np.array(indices_to_keep, dtype=np.intp)
            if self._embeddings is not None:
                self._embeddings = self._embeddings[keep_arr]
            self._documents = [self._documents[i] for i in indices_to_keep]
            self._metadata = [self._metadata[i] for i in indices_to_keep]

        logger.debug(
            "Deleted %d chunks matching %s=%s from VectorStore (remaining: %d)",
            deleted_count,
            key,
            value,
            len(self._documents),
        )
        return deleted_count

    def get_documents(self) -> list[str]:
        """Return a copy of all stored document chunk texts."""
        return list(self._documents)

    def get_metadata(self) -> list[dict[str, Any]]:
        """Return a copy of all stored chunk metadata dicts."""
        return list(self._metadata)

    def get_all_filenames(self) -> list[str]:
        """Return a sorted list of unique filenames currently stored."""
        seen = set()
        result: list[str] = []
        for meta in self._metadata:
            fname = meta.get("filename") or (Path(meta["source"]).name if meta.get("source") else None)
            if fname and fname not in seen:
                seen.add(fname)
                result.append(fname)
        return sorted(result)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        """
        Save the store to disk.

        Creates two files:
          {path}.npz  — compressed NumPy archive (embeddings matrix)
          {path}.json — document strings and metadata
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        # Save embeddings
        npz_path = p.with_suffix(".npz")
        if self._embeddings is not None:
            np.savez_compressed(str(npz_path), embeddings=self._embeddings)
        else:
            # Save an empty placeholder so load() succeeds
            np.savez_compressed(str(npz_path), embeddings=np.empty((0, 0), dtype=np.float32))

        # Save documents + metadata
        json_path = p.with_suffix(".json")
        payload = [
            {"document": doc, "metadata": meta} for doc, meta in zip(self._documents, self._metadata, strict=True)
        ]
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, path: str) -> None:
        """
        Load a previously saved store from disk, replacing current state.
        """
        p = Path(path)
        npz_path = p.with_suffix(".npz")
        json_path = p.with_suffix(".json")

        if not npz_path.exists():
            raise FileNotFoundError(f"Embeddings file not found: {npz_path}")
        if not json_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {json_path}")

        with np.load(str(npz_path)) as archive:
            loaded_embeddings = archive["embeddings"].astype(np.float32)

        if loaded_embeddings.size == 0:
            self._embeddings = None
        else:
            self._embeddings = loaded_embeddings

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self._documents = [item["document"] for item in payload]
        self._metadata = [item["metadata"] for item in payload]

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._documents)

    def __repr__(self) -> str:
        d = self._embeddings.shape[1] if self._embeddings is not None and self._embeddings.ndim == 2 else "?"
        return f"VectorStore(n={len(self)}, dim={d})"

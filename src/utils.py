"""
Shared utility functions used across pipeline components in DocMind AI.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from src.logger import get_logger

if TYPE_CHECKING:
    import torch

logger = get_logger(__name__)


def detect_device() -> str:
    """
    Auto-detect the best available torch device.

    Returns:
        "cuda", "mps", or "cpu".
    """
    import torch

    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    logger.debug("Detected optimal computation device: %s", device)
    return device


def load_hf_model(
    model_name: str,
    model_class: type,
    device: str | None = None,
) -> tuple[Any, Any, str]:
    """
    Load a HuggingFace model and tokenizer, set to eval mode, move to device.

    Shared by EmbeddingModel and CrossEncoderReranker to avoid duplicating
    the same init boilerplate (tokenizer + model + eval + device transfer).

    Args:
        model_name:  HuggingFace model ID.
        model_class: The transformers model class (e.g. AutoModel,
                     AutoModelForSequenceClassification).
        device:      "cuda", "mps", "cpu", or None for auto-detection.

    Returns:
        (tokenizer, model, device) tuple.
    """
    # pyrefly: ignore[missing-import]
    from transformers import AutoTokenizer

    device = device or detect_device()
    logger.debug("Loading Hugging Face model '%s' on device '%s'", model_name, device)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = model_class.from_pretrained(model_name)
    model.eval()
    model.to(device)
    return tokenizer, model, device


def move_to_device(tensor_dict: dict[str, torch.Tensor], device: str) -> dict[str, torch.Tensor]:
    """
    Move every tensor in a dict to the given device.

    Used after tokenizer encoding to transfer input_ids, attention_mask, etc.

    Args:
        tensor_dict: Dict of {str: torch.Tensor}.
        device:      Target device string.

    Returns:
        New dict with all tensors on *device*.
    """
    return {k: v.to(device) for k, v in tensor_dict.items()}


def resolve_path(path: str | Path) -> Path:
    """
    Resolve a path to its absolute form and verify it exists.

    Args:
        path: Filesystem path (relative or absolute).

    Returns:
        Resolved pathlib.Path.

    Raises:
        FileNotFoundError: If the resolved path does not exist.
    """
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    return p


def source_basename(meta: dict[str, Any]) -> str:
    """
    Extract a human-readable filename from chunk metadata.

    Supports both POSIX and Windows path separators across all host
    operating systems. Falls back to "unknown" if missing.

    Args:
        meta: Chunk metadata dict (expects a "source" key).

    Returns:
        Basename of the source path, or "unknown".
    """
    raw = meta.get("source", "unknown")
    if not raw or raw == "unknown":
        return "unknown"

    # Normalize backslashes to forward slashes so Path works uniformly across OSes
    normalized = str(raw).replace("\\", "/")
    name = Path(normalized).name
    return name if name else "unknown"


def top_k_indices(scores: np.ndarray, k: int) -> np.ndarray:
    """
    Return indices of the top-k highest scores, sorted descending.

    Uses argpartition for O(N) selection when k < N, falling back to
    full argsort when k == N.

    Args:
        scores: 1-D array of scores.
        k:      Number of top indices to return (clamped to len(scores)).

    Returns:
        np.ndarray of shape (k,) with indices into *scores*.
    """
    k = min(k, len(scores))
    if k == 0:
        return np.array([], dtype=np.intp)
    if k == len(scores):
        return np.argsort(scores)[::-1]
    partition = np.argpartition(scores, -k)[-k:]
    return partition[np.argsort(scores[partition])[::-1]]


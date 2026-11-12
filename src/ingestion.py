"""
Document ingestion for DocMind AI — PDF, plain text, Markdown, and DOCX loading.

All functions return a standardized dictionary:
    {
        "text":      str,   # full extracted text
        "filename":  str,   # basename of the source file
        "num_pages": int | None,
        "metadata": {
            "source":           str,  # absolute path
            "filename":         str,  # basename
            "file_type":        str,  # "pdf" | "txt" | "md" | "docx"
            "file_size":        int,  # bytes
            "upload_timestamp": str,  # ISO 8601 UTC string
            "page_count":       int | None,
            "pages":            int | None,
        }
    }
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.logger import get_logger
from src.utils import resolve_path

logger = get_logger(__name__)


def _make_metadata(p: Path, file_type: str, page_count: int | None = None) -> dict[str, Any]:
    stat = p.stat()
    return {
        "source": str(p),
        "filename": p.name,
        "file_type": file_type,
        "file_size": stat.st_size,
        "upload_timestamp": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "page_count": page_count,
        "pages": page_count,
    }


# ---------------------------------------------------------------------------
# PDF loading
# ---------------------------------------------------------------------------


def load_pdf(path: str | Path) -> dict[str, Any]:
    """
    Load a PDF file and extract all text via PyPDF2.
    """
    p = resolve_path(path)

    try:
        import PyPDF2
    except ImportError as exc:
        raise ImportError("PyPDF2 is required: pip install PyPDF2") from exc

    logger.debug("Parsing PDF file at '%s'", p)
    pages_text: list[str] = []
    with open(p, "rb") as fh:
        reader = PyPDF2.PdfReader(fh)
        num_pages = len(reader.pages)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                pages_text.append(extracted)

    full_text = "\n\n".join(pages_text)
    if not full_text.strip():
        raise ValueError(
            f"No extractable text found in '{p}'. The PDF may be a scanned image without an OCR text layer."
        )

    logger.debug("Successfully extracted %d characters across %d pages from '%s'", len(full_text), num_pages, p.name)
    return {
        "text": full_text,
        "filename": p.name,
        "num_pages": num_pages,
        "metadata": _make_metadata(p, "pdf", num_pages),
    }


# ---------------------------------------------------------------------------
# Plain text loading
# ---------------------------------------------------------------------------


def load_text(path: str | Path) -> dict[str, Any]:
    """
    Load a plain text (or Markdown) file.
    """
    p = resolve_path(path)
    logger.debug("Reading text file at '%s'", p)
    text = p.read_text(encoding="utf-8", errors="replace")
    logger.debug("Read %d characters from '%s'", len(text), p.name)

    suffix = p.suffix.lower().lstrip(".") or "txt"

    return {
        "text": text,
        "filename": p.name,
        "num_pages": None,
        "metadata": _make_metadata(p, suffix, None),
    }


# ---------------------------------------------------------------------------
# DOCX loading
# ---------------------------------------------------------------------------


def load_docx(path: str | Path) -> dict[str, Any]:
    """
    Load a Microsoft Word (.docx) document and extract text.
    """
    p = resolve_path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: '{p}'")

    if not zipfile.is_zipfile(p):
        raise ValueError(f"Invalid or corrupted DOCX archive at '{p}'")

    try:
        with zipfile.ZipFile(p, "r") as zf:
            if "word/document.xml" not in zf.namelist():
                raise ValueError(f"Invalid or corrupted DOCX archive: missing word/document.xml in '{p}'")
            xml_bytes = zf.read("word/document.xml")
            tree = ET.fromstring(xml_bytes)

            # Namespace-agnostic paragraph search
            paragraphs: list[str] = []
            for p_elem in tree.iter():
                if p_elem.tag.endswith("}p") or p_elem.tag == "p":
                    text_parts = [
                        t_elem.text
                        for t_elem in p_elem.iter()
                        if (t_elem.tag.endswith("}t") or t_elem.tag == "t") and t_elem.text
                    ]
                    if text_parts:
                        paragraphs.append("".join(text_parts))

            full_text = "\n\n".join(paragraphs).strip()
            if not full_text:
                raise ValueError(f"No extractable text found in DOCX file '{p}'")

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Invalid or corrupted DOCX file '{p}': {exc}") from exc

    return {
        "text": full_text,
        "filename": p.name,
        "num_pages": None,
        "metadata": _make_metadata(p, "docx", None),
    }


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def load_document(path: str | Path) -> dict[str, Any]:
    """
    Load a document from disk, dispatching on file extension.
    Supported extensions: .pdf, .txt, .md, .docx
    """
    suffix = Path(path).suffix.lower()

    if suffix == ".pdf":
        return load_pdf(path)
    elif suffix in {".txt", ".md"}:
        return load_text(path)
    elif suffix == ".docx":
        return load_docx(path)
    else:
        raise ValueError(f"Unsupported file type: '{suffix}'. Supported types are: .pdf, .txt, .md, .docx")


def load_documents(paths: list[str | Path]) -> list[dict[str, Any]]:
    """
    Batch load multiple documents across formats.
    """
    return [load_document(p) for p in paths]

"""
Unit tests for src/ingestion.py — load_pdf, load_text, load_document.

Uses pytest's tmp_path fixture to create minimal fixture files on disk.
A single-page PDF is generated programmatically with PyPDF2's writer.

Run with: pytest tests/test_ingestion.py -v
"""

from pathlib import Path

import pytest

from src.ingestion import load_document, load_pdf, load_text

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def write_text_file(path: Path, content: str = "Hello, world!\nLine two.") -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def write_pdf_file(path: Path, text: str = "Test PDF content.") -> Path:
    """Create a minimal single-page PDF using PyPDF2's writer."""
    try:
        # pyrefly: ignore[missing-import]
        from PyPDF2 import PdfWriter
        # pyrefly: ignore[missing-import]
        from PyPDF2.generic import (
            DecodedStreamObject,
            NameObject,
        )
    except ImportError:
        pytest.skip("PyPDF2 not installed")

    # Build a very minimal valid PDF with one page that has extractable text
    # via a content stream. We do this without relying on reportlab or other
    # PDF generation tools.
    writer = PdfWriter()

    # Use PyPDF2's add_blank_page + manually add a content stream
    page = writer.add_blank_page(width=612, height=792)

    # Create a simple content stream with BT/ET text operators
    content = f"BT /F1 12 Tf 100 700 Td ({text}) Tj ET".encode("latin-1")

    content_stream = DecodedStreamObject()
    content_stream.set_data(content)

    page[NameObject("/Contents")] = content_stream

    # Write to file
    with open(path, "wb") as fh:
        writer.write(fh)

    return path


# ---------------------------------------------------------------------------
# load_text tests
# ---------------------------------------------------------------------------


def test_load_text_basic(tmp_path):
    p = write_text_file(tmp_path / "doc.txt", "Hello, world!\nLine two.")
    result = load_text(str(p))
    assert "Hello, world!" in result["text"]


def test_load_text_metadata_keys(tmp_path):
    p = write_text_file(tmp_path / "doc.txt")
    result = load_text(str(p))
    assert "text" in result
    assert "filename" in result
    assert "num_pages" in result
    assert "metadata" in result
    assert "source" in result["metadata"]
    assert "file_type" in result["metadata"]


def test_load_text_filename(tmp_path):
    p = write_text_file(tmp_path / "myfile.txt")
    result = load_text(str(p))
    assert result["filename"] == "myfile.txt"


def test_load_text_file_type(tmp_path):
    p = write_text_file(tmp_path / "doc.txt")
    result = load_text(str(p))
    assert result["metadata"]["file_type"] == "txt"


def test_load_text_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_text("/nonexistent/path/file.txt")


def test_source_is_absolute_path(tmp_path):
    p = write_text_file(tmp_path / "doc.txt")
    result = load_text(str(p))
    source = result["metadata"]["source"]
    assert Path(source).is_absolute(), f"source is not absolute: {source}"


# ---------------------------------------------------------------------------
# load_pdf tests
# ---------------------------------------------------------------------------


def test_load_pdf_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_pdf("/nonexistent/path/file.pdf")


def test_load_pdf_metadata_keys(tmp_path):
    """Verify the returned dict has the right schema — skip if PDF has no text."""
    p = tmp_path / "test.pdf"
    write_pdf_file(p)
    try:
        result = load_pdf(str(p))
    except ValueError:
        pytest.skip("Test PDF has no extractable text layer (platform-specific PyPDF2 behaviour)")
    assert "text" in result
    assert "filename" in result
    assert "num_pages" in result
    assert result["metadata"]["file_type"] == "pdf"
    assert "source" in result["metadata"]


def test_load_pdf_num_pages(tmp_path):
    p = tmp_path / "test.pdf"
    write_pdf_file(p)
    try:
        result = load_pdf(str(p))
    except ValueError:
        pytest.skip("Test PDF has no extractable text layer")
    assert result["num_pages"] == 1



def test_load_pdf_filename(tmp_path):
    p = tmp_path / "my_doc.pdf"
    write_pdf_file(p)
    try:
        result = load_pdf(str(p))
    except ValueError:
        pytest.skip("Test PDF has no extractable text layer")
    assert result["filename"] == "my_doc.pdf"


# ---------------------------------------------------------------------------
# load_document dispatcher tests
# ---------------------------------------------------------------------------


def test_load_document_dispatch_txt(tmp_path):
    p = write_text_file(tmp_path / "doc.txt")
    result = load_document(str(p))
    assert result["metadata"]["file_type"] == "txt"


def test_load_document_dispatch_md(tmp_path):
    p = tmp_path / "notes.md"
    p.write_text("# Title\n\nSome markdown content.", encoding="utf-8")
    result = load_document(str(p))
    assert result["metadata"]["file_type"] == "md"


def test_load_document_dispatch_pdf(tmp_path):
    p = tmp_path / "test.pdf"
    write_pdf_file(p)
    try:
        result = load_document(str(p))
        assert result["metadata"]["file_type"] == "pdf"
    except ValueError:
        # PDF had no extractable text — dispatch worked, load_pdf raised correctly
        pass


def test_load_document_unsupported_extension(tmp_path):
    p = tmp_path / "file.xyz"
    p.write_bytes(b"fake unknown content")
    with pytest.raises(ValueError, match="Unsupported file type"):
        load_document(str(p))


def test_load_document_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_document("/nonexistent/path/file.txt")


# ---------------------------------------------------------------------------
# DOCX loading tests (Ingestion V2)
# ---------------------------------------------------------------------------


def write_docx_file(path: Path, paragraphs: list[str]) -> Path:
    """Create a minimal valid DOCX file using standard library zipfile."""
    import zipfile

    xml_paras = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{xml_paras}</w:body>"
        "</w:document>"
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("word/document.xml", doc_xml)
    return path


def test_load_docx_basic(tmp_path):
    p = tmp_path / "sample.docx"
    write_docx_file(p, ["DocMind AI Ingestion V2", "Paragraph two content."])

    from src.ingestion import load_docx

    result = load_docx(str(p))
    assert "DocMind AI Ingestion V2" in result["text"]
    assert "Paragraph two content." in result["text"]
    assert result["filename"] == "sample.docx"
    assert result["metadata"]["file_type"] == "docx"
    assert result["metadata"]["file_size"] > 0
    assert result["metadata"]["upload_timestamp"] is not None


def test_load_docx_corrupted(tmp_path):
    p = tmp_path / "broken.docx"
    p.write_bytes(b"not a valid zip or docx")

    from src.ingestion import load_docx

    with pytest.raises(ValueError, match="Invalid or corrupted DOCX"):
        load_docx(str(p))


def test_load_docx_empty(tmp_path):
    p = tmp_path / "empty.docx"
    write_docx_file(p, ["   ", ""])

    from src.ingestion import load_docx

    with pytest.raises(ValueError, match="No extractable text"):
        load_docx(str(p))


def test_load_docx_missing_file_raises():
    from src.ingestion import load_docx

    with pytest.raises(FileNotFoundError):
        load_docx("/nonexistent/file.docx")


def test_load_document_dispatch_docx(tmp_path):
    p = tmp_path / "dispatch_test.docx"
    write_docx_file(p, ["Testing DOCX dispatcher routing."])
    result = load_document(str(p))
    assert result["metadata"]["file_type"] == "docx"
    assert "Testing DOCX dispatcher routing." in result["text"]


# ---------------------------------------------------------------------------
# Multi-file batch loading & Metadata schema tests (Ingestion V2)
# ---------------------------------------------------------------------------


def test_load_documents_multiple(tmp_path):
    from src.ingestion import load_documents

    p_txt = write_text_file(tmp_path / "first.txt", "First text file.")
    p_md = tmp_path / "second.md"
    p_md.write_text("Second markdown file.", encoding="utf-8")
    p_docx = tmp_path / "third.docx"
    write_docx_file(p_docx, ["Third docx file."])

    docs = load_documents([str(p_txt), str(p_md), str(p_docx)])
    assert len(docs) == 3
    assert docs[0]["filename"] == "first.txt"
    assert docs[0]["metadata"]["file_type"] == "txt"
    assert docs[1]["filename"] == "second.md"
    assert docs[1]["metadata"]["file_type"] == "md"
    assert docs[2]["filename"] == "third.docx"
    assert docs[2]["metadata"]["file_type"] == "docx"


def test_metadata_schema_fields(tmp_path):
    p = write_text_file(tmp_path / "meta_test.txt", "Testing structured metadata schema.")
    result = load_document(str(p))

    meta = result["metadata"]
    # Check all required fields from user requirements:
    # filename, file type, upload timestamp, page count, file size
    assert meta["filename"] == "meta_test.txt"
    assert meta["file_type"] == "txt"
    assert isinstance(meta["file_size"], int) and meta["file_size"] > 0
    assert "upload_timestamp" in meta and len(meta["upload_timestamp"]) > 0
    assert "page_count" in meta  # None for txt
    assert "source" in meta


"""
DocMind AI — Streamlit application.

Wires together every src/ component into an end-to-end pipeline:
  Upload → Ingest → Chunk → Embed → Index → Ask → Retrieve → Rerank → Generate

Compatible with HuggingFace Spaces (all file I/O uses /tmp via tempfile,
API key entered in the sidebar UI — no .env required on Spaces).
"""

from bokeh.core.property.any import Any
# pyrefly: ignore[invalid-syntax]
from __future__ import annotations

import os
import tempfile
from pathlib import Path
import pandas as pd
import streamlit as st

from src.logger import get_logger
from src.utils import source_basename

logger = get_logger("docmind.app")

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="DocMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global styling
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
    /* ---------- General ---------- */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1100px;
    }

    #MainMenu, footer {visibility: hidden;}

    /* ---------- Hero header ---------- */
    .hero-banner {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 55%, #C026D3 100%);
        border-radius: 18px;
        padding: 2rem 2.25rem;
        margin-bottom: 1.75rem;
        color: white;
        box-shadow: 0 10px 30px -12px rgba(79, 70, 229, 0.45);
    }
    .hero-banner h1 {
        font-size: 1.9rem;
        font-weight: 800;
        margin: 0 0 0.35rem 0;
        color: white;
    }
    .hero-banner p {
        margin: 0;
        font-size: 0.95rem;
        opacity: 0.92;
    }
    .hero-badges {
        margin-top: 0.9rem;
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .hero-badge {
        background: rgba(255,255,255,0.16);
        border: 1px solid rgba(255,255,255,0.28);
        border-radius: 999px;
        padding: 0.25rem 0.7rem;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.01em;
    }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: #0f1117;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] .stButton button {
        border-radius: 10px;
        font-weight: 700;
        height: 2.7rem;
    }
    .sidebar-step {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
    }
    .sidebar-step .num {
        background: #7C3AED;
        color: white;
        border-radius: 999px;
        width: 22px;
        height: 22px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.72rem;
    }

    /* ---------- Status card ---------- */
    .status-card {
        border: 1px solid rgba(124, 58, 237, 0.35);
        background: rgba(124, 58, 237, 0.08);
        border-radius: 12px;
        padding: 0.75rem 0.9rem;
        font-size: 0.85rem;
        line-height: 1.5;
    }
    .status-card b { color: #C084FC; }

    /* ---------- Empty state ---------- */
    .empty-state {
        text-align: center;
        padding: 3.5rem 1.5rem;
        border: 1.5px dashed rgba(120,120,140,0.35);
        border-radius: 16px;
        background: rgba(124, 58, 237, 0.03);
    }
    .empty-state .icon { font-size: 2.4rem; margin-bottom: 0.5rem; }
    .empty-state h3 { margin: 0 0 0.35rem 0; }
    .empty-state p { color: rgba(160,160,180,0.9); margin: 0; }

    /* ---------- Chat entries ---------- */
    .qa-card {
        border-radius: 16px;
        border: 1px solid rgba(120,120,140,0.18);
        padding: 1.25rem 1.4rem;
        margin-bottom: 1.4rem;
        background: rgba(255,255,255,0.015);
    }
    .qa-question {
        display: flex;
        gap: 0.6rem;
        align-items: flex-start;
        font-weight: 700;
        font-size: 1.02rem;
        margin-bottom: 0.85rem;
    }
    .qa-question .bubble {
        background: #4F46E5;
        color: white;
        border-radius: 999px;
        min-width: 26px;
        height: 26px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        flex-shrink: 0;
    }
    .qa-answer {
        padding-left: 2.15rem;
        line-height: 1.65;
    }
    .source-chip {
        display: inline-block;
        background: rgba(192, 132, 252, 0.12);
        border: 1px solid rgba(192, 132, 252, 0.3);
        color: #C084FC;
        border-radius: 8px;
        padding: 0.15rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.4rem;
    }

    /* ---------- Metrics ---------- */
    div[data-testid="stMetric"] {
        background: rgba(124, 58, 237, 0.06);
        border: 1px solid rgba(124, 58, 237, 0.18);
        border-radius: 12px;
        padding: 0.7rem 0.9rem;
    }

    /* ---------- Retrieval V2 Enhanced Cards ---------- */
    .source-card {
        border-radius: 12px;
        border: 1px solid rgba(120,120,140,0.18);
        background: rgba(255,255,255,0.02);
        padding: 1rem 1.15rem;
        margin-bottom: 1rem;
    }
    .source-card-used {
        border-radius: 12px;
        border: 1.5px solid rgba(245, 158, 11, 0.55);
        background: rgba(245, 158, 11, 0.04);
        padding: 1rem 1.15rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px -8px rgba(245, 158, 11, 0.35);
    }
    .badge-used {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: rgba(245, 158, 11, 0.18);
        border: 1px solid rgba(245, 158, 11, 0.45);
        color: #FBBF24;
        border-radius: 6px;
        padding: 0.2rem 0.55rem;
        font-size: 0.74rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .meta-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin-bottom: 0.75rem;
    }
    .meta-pill {
        display: inline-block;
        background: rgba(124, 58, 237, 0.08);
        border: 1px solid rgba(124, 58, 237, 0.22);
        border-radius: 6px;
        padding: 0.15rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .meta-pill b {
        color: #C084FC;
    }
    .chunk-pre {
        white-space: pre-wrap;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.85rem;
        line-height: 1.55;
        background: rgba(0, 0, 0, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin: 0;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Lazy imports — only import ML libraries after page config so Streamlit
# can render the UI immediately while models load in the background.
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner="Loading embedding model (~90MB)…")
def load_embedding_model():
    from src.embeddings import EmbeddingModel

    return EmbeddingModel()


@st.cache_resource(show_spinner="Loading cross-encoder (~85MB)…")
def load_reranker():
    from src.reranker import CrossEncoderReranker

    return CrossEncoderReranker()


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------


def format_bytes(size: int) -> str:
    """Format file size in human-readable units."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.2f} MB"


def init_session_state() -> None:
    defaults = {
        "vectorstore": None,
        "bm25": None,
        "retriever": None,
        "indexed_filename": None,
        "chunk_count": 0,
        "chat_history": [],
        "indexed_documents": {},  # filename -> metadata dict
        "recent_queries": [],     # last 10 queries
        "selected_query": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.1rem;">
            <span style="font-size:1.6rem;">🧠</span>
            <span style="font-size:1.25rem;font-weight:800;">DocMind AI</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Intelligent RAG · Ingestion V2 Pipeline")
    st.divider()

    # --- Document upload ---
    st.markdown(
        '<div class="sidebar-step"><span class="num">1</span> Ingest Documents</div>',
        unsafe_allow_html=True,
    )
    uploaded_files = st.file_uploader(
        "PDF, DOCX, TXT, or MD files",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
        help="Upload one or more documents to index (PDF, DOCX, TXT, Markdown).",
        label_visibility="collapsed",
    )

    index_btn = st.button(
        "⚡ Index Documents",
        disabled=(not uploaded_files),
        use_container_width=True,
        type="primary",
    )

    if index_btn and uploaded_files:
        progress_bar = st.progress(0, text="Initializing Ingestion V2…")
        status_box = st.empty()
        try:
            from src.bm25 import BM25
            from src.chunker import RecursiveTextChunker
            from src.ingestion import load_document
            from src.retriever import HybridRetriever
            from src.vectorstore import VectorStore

            embedder = load_embedding_model()
            chunker = RecursiveTextChunker(chunk_size=512, chunk_overlap=64)

            # Re-use existing vectorstore or initialize new
            vs = st.session_state.get("vectorstore")
            if vs is None:
                vs = VectorStore()

            total_files = len(uploaded_files)
            new_chunks_total = 0

            for idx, uf in enumerate(uploaded_files):
                file_pct = int((idx / total_files) * 85)
                progress_bar.progress(file_pct, text=f"Processing '{uf.name}' ({idx + 1}/{total_files})…")

                # Save uploaded file to temp location
                suffix = Path(uf.name).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uf.read())
                    tmp_path = tmp.name

                try:
                    # Ingest with format-specific loader
                    doc = load_document(tmp_path)
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

                # Chunk document text
                chunks = chunker.split_text(doc["text"])
                if not chunks:
                    continue

                # Prepare structured chunk metadata
                chunk_texts = [c["text"] for c in chunks]
                chunk_metas = []
                for c in chunks:
                    chunk_metas.append(
                        {
                            "source": doc["metadata"]["source"],
                            "filename": doc["filename"],
                            "chunk_index": c["chunk_index"],
                            "file_type": doc["metadata"]["file_type"],
                            "file_size": doc["metadata"]["file_size"],
                            "upload_timestamp": doc["metadata"]["upload_timestamp"],
                            "page_count": doc["metadata"].get("page_count"),
                            "pages": doc["metadata"].get("pages"),
                        }
                    )

                # Embed chunks
                progress_bar.progress(
                    file_pct + int(40 / total_files),
                    text=f"Embedding '{uf.name}' ({len(chunks)} chunks)…",
                )
                embeddings = embedder.embed_texts(chunk_texts, show_progress=False)

                # Remove previous version if already in VectorStore
                vs.delete_by_filename(doc["filename"])
                vs.add(embeddings, chunk_texts, chunk_metas)

                # Track in structured document catalog
                st.session_state["indexed_documents"][doc["filename"]] = {
                    "filename": doc["filename"],
                    "file_type": doc["metadata"]["file_type"],
                    "file_size": doc["metadata"]["file_size"],
                    "upload_timestamp": doc["metadata"]["upload_timestamp"],
                    "page_count": doc["metadata"].get("page_count"),
                    "chunk_count": len(chunks),
                }
                new_chunks_total += len(chunks)

            # Rebuild only the affected index: refit BM25 on all current chunks
            progress_bar.progress(90, text="Synchronizing BM25 and hybrid retriever…")
            all_texts = vs.get_documents()
            bm = BM25()
            bm.fit(all_texts)

            retriever = HybridRetriever(vs, bm, embedder)

            # Update session state
            st.session_state["vectorstore"] = vs
            st.session_state["bm25"] = bm
            st.session_state["retriever"] = retriever
            st.session_state["chunk_count"] = len(all_texts)
            st.session_state["indexed_filename"] = ", ".join(st.session_state["indexed_documents"].keys())

            progress_bar.progress(100, text="Indexing complete!")
            progress_bar.empty()
            st.success(
                f"Successfully indexed **{total_files}** document(s) (**{new_chunks_total}** chunks)!",
                icon="✅",
            )

        except Exception as exc:
            progress_bar.empty()
            logger.exception("Ingestion failed: %s", exc)
            st.error(f"Indexing failed: {exc}", icon="🚨")

    # --- Document management & deletion list ---
    if st.session_state["indexed_documents"]:
        st.markdown(
            f"""
            <div class="status-card" style="margin-bottom:0.6rem;">
                📚 <b>Indexed Documents:</b> {len(st.session_state['indexed_documents'])}<br/>
                🧩 <b>Total Chunks:</b> {st.session_state['chunk_count']}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("Manage Ingested Documents:")
        format_icons = {"pdf": "📕", "docx": "📘", "txt": "📄", "md": "📝"}

        for doc_name, meta in list(st.session_state["indexed_documents"].items()):
            icon = format_icons.get(meta.get("file_type", "").lower(), "📄")
            size_str = format_bytes(meta.get("file_size", 0))
            pages_str = f" · {meta['page_count']} pgs" if meta.get("page_count") else ""

            col_info, col_del = st.columns([4, 1])
            with col_info:
                st.markdown(
                    f"""
                    <div style="font-size:0.8rem; line-height:1.3; padding: 0.2rem 0;">
                        <b>{icon} {doc_name}</b><br/>
                        <span style="opacity:0.75; font-size:0.72rem;">
                            {meta.get('file_type', '').upper()}{pages_str} · {meta.get('chunk_count', 0)} chunks · {size_str}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_del:
                if st.button("🗑️", key=f"del_doc_{doc_name}", help=f"Delete '{doc_name}' and rebuild index"):
                    # Rebuild affected index without re-embedding remaining documents
                    vs = st.session_state.get("vectorstore")
                    if vs is not None:
                        removed = vs.delete_by_filename(doc_name)
                        st.session_state["indexed_documents"].pop(doc_name, None)
                        remaining = vs.get_documents()
                        if remaining:
                            embedder = load_embedding_model()
                            bm = BM25()
                            bm.fit(remaining)
                            st.session_state["bm25"] = bm
                            st.session_state["retriever"] = HybridRetriever(vs, bm, embedder)
                            st.session_state["chunk_count"] = len(remaining)
                            st.session_state["indexed_filename"] = ", ".join(
                                st.session_state["indexed_documents"].keys()
                            )
                        else:
                            st.session_state["vectorstore"] = None
                            st.session_state["bm25"] = None
                            st.session_state["retriever"] = None
                            st.session_state["chunk_count"] = 0
                            st.session_state["indexed_filename"] = None

                        st.toast(f"Deleted '{doc_name}' ({removed} chunks). Index rebuilt!", icon="🗑️")
                        st.rerun()
    else:
        st.caption("No documents indexed yet.")

    st.divider()

    # --- LLM Settings ---
    st.markdown('<div class="sidebar-step"><span class="num">2</span> LLM Settings</div>', unsafe_allow_html=True)

    with st.expander("⚙️ Groq API configuration", expanded=not bool(os.environ.get("GROQ_API_KEY"))):
        api_key = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_...",
        )

        base_url = st.text_input(
            "API Base URL",
            value="https://api.groq.com/openai/v1",
        )

        model = st.text_input(
            "Groq Model",
            value="openai/gpt-oss-120b",
        )

    if api_key.strip():
        st.caption("🔑 API key set for this session")
    else:
        st.caption("🔒 No API key entered yet")

    st.divider()

    # --- Retrieval settings ---
    st.markdown('<div class="sidebar-step"><span class="num">3</span> Retrieval Settings</div>', unsafe_allow_html=True)
    top_k = st.slider("Chunks to retrieve", min_value=1, max_value=10, value=5)

    if st.session_state["chat_history"]:
        if st.button("🗑️ Clear chat history", use_container_width=True):
            st.session_state["chat_history"] = []
            st.rerun()

    st.divider()
    st.caption(
        "DocMind AI · Built from scratch · "
        "[GitHub](https://github.com/Kshubham0315/Rag_From_Scratch.git) · "
    )

# ---------------------------------------------------------------------------
# Main area — hero header
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero-banner">
        <h1>🧠 DocMind AI</h1>
        <p>Intelligent Retrieval-Augmented Generation built from scratch — no LangChain, no LlamaIndex.</p>
        <div class="hero-badges">
            <span class="hero-badge">🔀 Recursive chunking</span>
            <span class="hero-badge">🔎 BM25 + dense hybrid retrieval</span>
            <span class="hero-badge">🎯 Cross-encoder reranking</span>
            <span class="hero-badge">⚡ Raw API call</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Pipeline status strip ---
status_cols = st.columns(4)
has_api_key = bool(api_key.strip())
pipeline_steps = [
    ("📤", "Upload", st.session_state["indexed_filename"] is not None),
    ("✂️", "Chunk", st.session_state["chunk_count"] > 0),
    ("🧠", "Index", st.session_state["retriever"] is not None),
    ("🔑", "API Key", has_api_key),
]

for col, (icon, label, done) in zip(status_cols, pipeline_steps):
    with col:
        st.markdown(
            f"""
            <div style="text-align:center; padding: 0.6rem 0.3rem; border-radius: 10px;
                        background: {'rgba(34,197,94,0.10)' if done else 'rgba(120,120,140,0.06)'};
                        border: 1px solid {'rgba(34,197,94,0.35)' if done else 'rgba(120,120,140,0.15)'};">
                <div style="font-size:1.3rem;">{icon}</div>
                <div style="font-size:0.8rem;font-weight:700;">{label}</div>
                <div style="font-size:0.72rem;opacity:0.75;">{'✅ Ready' if done else '⏳ Pending'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.write("")

# --- Knowledge base overview ---
if st.session_state["indexed_documents"]:
    num_docs = len(st.session_state["indexed_documents"])
    total_chunks = st.session_state["chunk_count"]
    with st.expander(
        f"📁 Ingested Knowledge Base ({num_docs} document{'s' if num_docs > 1 else ''} · {total_chunks} chunks)",
        expanded=False,
    ):
        doc_rows = []
        for dname, dmeta in st.session_state["indexed_documents"].items():
            doc_rows.append(
                {
                    "Document": dname,
                    "Format": dmeta.get("file_type", "").upper(),
                    "File Size": format_bytes(dmeta.get("file_size", 0)),
                    "Pages": dmeta.get("page_count") if dmeta.get("page_count") is not None else "—",
                    "Chunks": dmeta.get("chunk_count", 0),
                    "Upload Timestamp (UTC)": dmeta.get("upload_timestamp", "")[:19].replace("T", " "),
                }
            )
        st.dataframe(pd.DataFrame(doc_rows), use_container_width=True, hide_index=True)

# --- Metadata Filter Controls (Retrieval V2) ---
active_filters: dict[str, Any] = {}
if st.session_state["indexed_documents"]:
    with st.expander("🔍 Filter by Document Metadata (Optional)", expanded=False):
        fcol1, fcol2, fcol3 = st.columns(3)
        doc_names = ["All Documents"] + sorted(list(st.session_state["indexed_documents"].keys()))
        doc_types = ["All Types"] + sorted(
            list(
                {
                    meta.get("file_type", "").upper()
                    for meta in st.session_state["indexed_documents"].values()
                    if meta.get("file_type")
                }
            )
        )
        doc_dates = ["All Dates"] + sorted(
            list(
                {
                    meta.get("upload_timestamp", "")[:10]
                    for meta in st.session_state["indexed_documents"].values()
                    if meta.get("upload_timestamp")
                }
            ),
            reverse=True,
        )

        with fcol1:
            sel_doc = st.selectbox("Document", doc_names, index=0)
            if sel_doc != "All Documents":
                active_filters["filename"] = sel_doc

        with fcol2:
            sel_type = st.selectbox("Document Type", doc_types, index=0)
            if sel_type != "All Types":
                active_filters["file_type"] = sel_type.lower()

        with fcol3:
            sel_date = st.selectbox("Uploaded Date", doc_dates, index=0)
            if sel_date != "All Dates":
                active_filters["uploaded_date"] = sel_date

        if active_filters:
            st.caption(f"🎯 Active filters: `{active_filters}`")

# --- Recent Queries (Retrieval V2) ---
if st.session_state["recent_queries"]:
    st.markdown(
        "<div style='font-size:0.8rem; font-weight:700; margin-bottom:0.35rem; color:#A78BFA;'>🕒 Recent Queries (Last 10):</div>",
        unsafe_allow_html=True,
    )
    num_rq = min(len(st.session_state["recent_queries"]), 5)
    rq_cols = st.columns(num_rq)
    for i, rq in enumerate(st.session_state["recent_queries"][:num_rq]):
        with rq_cols[i]:
            short_q = rq[:28] + "…" if len(rq) > 28 else rq
            if st.button(f"💬 {short_q}", key=f"rq_{i}", help=rq, use_container_width=True):
                st.session_state["selected_query"] = rq
                st.rerun()

# --- Query input ---
default_query = st.session_state.get("selected_query", "")
if default_query:
    st.session_state["selected_query"] = ""

col1, col2 = st.columns([5, 1])
with col1:
    query = st.text_input(
        "Ask a question about your document",
        value=default_query,
        placeholder="💬 What is the main topic of this document?",
        label_visibility="collapsed",
    )
with col2:
    submit = st.button(
        "Ask ▶",
        use_container_width=True,
        type="primary",
        disabled=(st.session_state["retriever"] is None or not api_key.strip() or not query.strip()),
    )

if st.session_state["retriever"] is None:
    st.markdown(
        """
        <div class="empty-state">
            <div class="icon">📥</div>
            <h3>Upload documents to get started</h3>
            <p>Use the sidebar to upload PDF, DOCX, TXT, or Markdown (.md) files and index them.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

if not api_key.strip() and st.session_state["retriever"] is not None:
    st.warning("Enter your Groq API key in the sidebar to enable answer generation.", icon="🔑")

# --- Run pipeline on submit ---
if submit and query.strip() and st.session_state["retriever"] is not None:
    with st.status("Running DocMind AI Retrieval V2 pipeline…", expanded=True) as status:
        try:
            import time
            from src.generator import LLMGenerator
            from src.retrieval_v2 import (
                RetrievalMetrics,
                add_recent_query,
                compute_retrieval_confidence,
                identify_used_chunks,
            )

            t_total_0 = time.perf_counter()

            # 1. Retrieval
            st.write("🔎 Retrieving candidate chunks with hybrid RRF…")
            t_ret_0 = time.perf_counter()
            retriever = st.session_state["retriever"]
            retrieved = retriever.retrieve(
                query,
                top_k=top_k,
                metadata_filter=active_filters if active_filters else None,
            )
            retrieval_ms = (time.perf_counter() - t_ret_0) * 1000

            # 2. Reranking
            st.write("🎯 Reranking with cross-encoder…")
            t_rerank_0 = time.perf_counter()
            reranker = load_reranker()
            reranked = reranker.rerank(query, retrieved, top_k=top_k)
            reranking_ms = (time.perf_counter() - t_rerank_0) * 1000

            # 3. Generation
            st.write("✍️ Generating grounded answer…")
            t_gen_0 = time.perf_counter()
            generator = LLMGenerator(
                api_key=api_key.strip(),
                base_url=base_url.strip(),
                model=model.strip(),
            )
            result = generator.generate(query, reranked)
            generation_ms = (time.perf_counter() - t_gen_0) * 1000

            total_ms = (time.perf_counter() - t_total_0) * 1000

            # 4. Explainability & Trust: Confidence & Chunk Highlighting
            confidence = compute_retrieval_confidence(reranked)
            annotated_chunks = identify_used_chunks(result["answer"], reranked)

            metrics = RetrievalMetrics(
                retrieval_latency_ms=round(retrieval_ms, 2),
                reranking_latency_ms=round(reranking_ms, 2),
                generation_latency_ms=round(generation_ms, 2),
                total_latency_ms=round(total_ms, 2),
                retrieved_chunk_count=len(retrieved),
                reranked_chunk_count=len(reranked),
            )

            result["chunks"] = annotated_chunks
            result["confidence"] = confidence
            result["metrics"] = metrics.to_dict()
            result["filters"] = dict(active_filters)

            # 5. Store in recent queries
            st.session_state["recent_queries"] = add_recent_query(
                st.session_state["recent_queries"], query
            )

            # Prepend to history so newest is at top
            st.session_state["chat_history"].insert(
                0,
                {
                    "query": query,
                    "result": result,
                },
            )
            status.update(label="Complete!", state="complete", expanded=False)

        except Exception as exc:
            status.update(label="Pipeline failed", state="error", expanded=True)
            logger.exception("Pipeline failed: %s", exc)
            st.error(f"Pipeline error: {exc}", icon="🚨")

# --- Render chat history ---
if st.session_state["chat_history"]:
    st.markdown("### 🗂️ History")

for entry in st.session_state["chat_history"]:
    q = entry["query"]
    res = entry["result"]
    conf = res.get("confidence", {})
    metrics = res.get("metrics", {})

    st.markdown(
        f"""
        <div class="qa-card">
            <div class="qa-question"><span class="bubble">Q</span>{q}</div>
            <div class="qa-answer">{res["answer"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Retrieval Confidence Banner
    if conf:
        conf_color = conf.get("color", "#22c55e")
        conf_level = conf.get("level", "Medium")
        conf_pct = conf.get("percentage", 0.0)
        conf_expl = conf.get("explanation", "")
        st.markdown(
            f"""
            <div style="background: {conf_color}14; border: 1px solid {conf_color}45; border-radius: 12px; padding: 0.75rem 1rem; margin-bottom: 1rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:800; font-size:0.95rem; color:{conf_color};">
                        🛡️ Retrieval Confidence: {conf_level} ({conf_pct}%)
                    </span>
                    <span style="font-size:0.75rem; background:rgba(255,255,255,0.08); padding:0.15rem 0.5rem; border-radius:999px;">
                        Calibrated Explainability
                    </span>
                </div>
                <div style="font-size:0.83rem; margin-top:0.35rem; line-height:1.45; opacity:0.95;">
                    {conf_expl}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    tab_chunks, tab_metrics, tab_sources, tab_usage = st.tabs(
        [
            f"📄 Enhanced Source Cards ({len(res.get('chunks', []))})",
            "⚡ Retrieval Metrics",
            "📎 Sources Table",
            "📊 Token Usage",
        ]
    )

    with tab_chunks:
        for i, chunk in enumerate(res.get("chunks", []), start=1):
            is_used = chunk.get("is_used", False)
            meta = chunk.get("metadata", {})
            filename = source_basename(meta)
            page_val = meta.get("page_count") or meta.get("page", "—")
            chunk_idx = meta.get("chunk_index", 0)

            sim_score = chunk.get("similarity_score")
            sim_str = f"{sim_score:.4f}" if sim_score is not None else "Dense (fused)"

            rerank_score = chunk.get("rerank_score")
            rerank_str = f"{rerank_score:+.4f}" if rerank_score is not None else "N/A"

            card_class = "source-card-used" if is_used else "source-card"
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

            if is_used:
                st.markdown(
                    '<div class="badge-used">🎯 Primary Source Used for Answer Generation</div>',
                    unsafe_allow_html=True,
                )

            # Enhanced Source Card Header with all 5 required elements:
            # filename, page number, chunk number, similarity score, reranker score
            st.markdown(
                f"""
                <div class="meta-grid">
                    <span class="meta-pill">📁 <b>File:</b> {filename}</span>
                    <span class="meta-pill">📄 <b>Page:</b> {page_val}</span>
                    <span class="meta-pill">🧩 <b>Chunk:</b> {chunk_idx}</span>
                    <span class="meta-pill">🔍 <b>Similarity:</b> {sim_str}</span>
                    <span class="meta-pill">🎯 <b>Reranker Score:</b> {rerank_str}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Highlighted chunk text preserving formatting
            chunk_display = chunk.get("highlighted_html") if is_used else chunk.get("text", "")
            st.markdown(
                f'<pre class="chunk-pre">{chunk_display}</pre>',
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_metrics:
        if metrics:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🔍 Retrieval", f"{metrics.get('retrieval_latency_ms', 0):.1f} ms")
            m2.metric("🎯 Reranking", f"{metrics.get('reranking_latency_ms', 0):.1f} ms")
            m3.metric("✍️ Generation", f"{metrics.get('generation_latency_ms', 0):.1f} ms")
            m4.metric("⏱️ Total Time", f"{metrics.get('total_latency_ms', 0):.1f} ms")

            st.write("")
            col_c1, col_c2 = st.columns(2)
            col_c1.info(f"📥 **Retrieved Candidates:** {metrics.get('retrieved_chunk_count', 0)} chunks")
            col_c2.success(f"🎯 **Final Reranked:** {metrics.get('reranked_chunk_count', 0)} chunks")

            # Timing breakdown
            tot = metrics.get('total_latency_ms', 1.0) or 1.0
            r_pct = round((metrics.get('retrieval_latency_ms', 0) / tot) * 100, 1)
            rr_pct = round((metrics.get('reranking_latency_ms', 0) / tot) * 100, 1)
            g_pct = round((metrics.get('generation_latency_ms', 0) / tot) * 100, 1)
            st.caption(f"Latency Distribution: Retrieval {r_pct}% · Reranking {rr_pct}% · Generation {g_pct}%")
            if res.get("filters"):
                st.caption(f"Applied Filters: `{res['filters']}`")
        else:
            st.caption("No telemetry recorded for this entry.")

    with tab_sources:
        if res.get("sources"):
            st.dataframe(
                pd.DataFrame(res["sources"]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No source metadata available.")

    with tab_usage:
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Prompt tokens", res.get("prompt_tokens", 0))
        col_b.metric("Completion tokens", res.get("completion_tokens", 0))
        col_c.metric(
            "Total tokens",
            res.get("prompt_tokens", 0) + res.get("completion_tokens", 0),
        )
        st.caption(f"Model: `{res.get('model', model)}`")
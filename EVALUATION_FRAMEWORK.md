# DocMind AI — Enterprise RAG Evaluation Framework (`v1.7.0`)

## 1. Architecture Overview

The **DocMind AI Evaluation Framework** (Sprint 6.0) is implemented as a strict **non-intrusive observability layer** (`backend/app/services/evaluation_service.py`) that evaluates every completed RAG interaction asynchronously without altering retrieval rankings, chunks, reranker scores, confidence scores, prompts, or generated answers.

### Key Architectural Guarantees
- **Zero Pipeline Interference**: Runs post-generation via FastAPI `BackgroundTasks` (and isolated synchronous calls during benchmarks).
- **Low Overhead**: Pure in-memory lexical, structural, and IR metric computation completes in **< 5 ms** per query (strictly below the `15 ms` ceiling).
- **Persistent Telemetry**: Results are stored in SQLite (`evaluation_history`) alongside stage latencies and token usage.

---

## 2. Pipeline Flow

```text
User Query
   ↓
Query Rewriter (Sprint 4.3.5)
   ↓
Adaptive Retrieval Planner (Sprint 4.4)
   ↓
Hybrid Retrieval (Dense BGE + BM25 + RRF k=60)
   ↓
Cross-Encoder Reranker (ms-marco-MiniLM-L-6-v2)
   ↓
LLM Generation (Gemini → Groq Fallback) & Citations
   ↓
[HTTP Response Returned to User]
   ↓ (Async Background Observer)
EvaluationService
   ├─ Retrieval Quality (Precision@K, Recall@K, MRR, DCG/IDCG/NDCG, Coverage, Diversity)
   ├─ Generation Quality (Grounding, Faithfulness, Citation Coverage, Hallucination Risk)
   ├─ Citation Verification (Non-destructive [Source N] audit, warnings only)
   └─ SQLite Persistence (evaluation_history)
```

---

## 3. Metric Definitions & Mathematical Formulas

### Retrieval Metrics
- **Precision@K**:
  $$\text{Precision}@K = \frac{|\text{Relevant} \cap \text{Top-}K|}{K}$$
- **Recall@K**:
  $$\text{Recall}@K = \frac{|\text{Relevant} \cap \text{Top-}K|}{|\text{Total Relevant}|}$$
- **Mean Reciprocal Rank (MRR)**:
  $$\text{MRR} = \frac{1}{\text{rank}_1}$$
  where $\text{rank}_1$ is the 1-based position of the first relevant retrieved chunk ($0.0$ if none).
- **DCG, IDCG, and NDCG**:
  $$\text{DCG}@K = \sum_{i=1}^{K} \frac{2^{rel_i} - 1}{\log_2(i + 1)}, \qquad \text{IDCG}@K = \sum_{i=1}^{K} \frac{2^{rel^*_i} - 1}{\log_2(i + 1)}, \qquad \text{NDCG}@K = \frac{\text{DCG}@K}{\text{IDCG}@K}$$
- **Context Recall** ($0 \rightarrow 100$): Percentage of retrieved chunks actively utilized in the answer via citation or lexical alignment.
- **Retrieval Coverage** ($0 \rightarrow 100$): Percentage of uploaded documents contributing chunks to the response.
- **Source Diversity**: Number of unique filenames contributing chunks.

### Generation Quality Metrics (Normalized $0 \rightarrow 100$)
- **Grounding Score**: Content-token alignment ratio between the answer and retrieved chunks plus valid citation credit.
- **Faithfulness**: Percentage of answer sentences grounded in retrieved context chunks.
- **Citation Coverage**: Combined sentence citation rate and verified citation integrity.
- **Context Utilization**: Percentage of provided context chunks reflected in the generated output.
- **Answer Completeness**: Coverage of query/expected keywords combined with response completeness.
- **Hallucination Risk**: Inverse of faithfulness/grounding adjusted by citation warnings (lower is better).
- **Source Utilization**: Percentage of returned sources explicitly cited via `[Source N]`.
- **Answer Length**: Word count of the generated response.
- **Reasoning Coverage**: Explanatory structure, reasoning connectives, and depth.

### Citation Verification
Audits every `[Source N]` reference without modifying the answer:
- Checks citation index bounds (`citation_exists`, `chunk_exists`)
- Validates metadata (`filename`, `page_number`, `chunk_index`)
- Verifies lexical overlap between citing sentence and source chunk text (`chunk_text_matches`)
- Emits non-destructive `warnings` only.

---

## 4. Backend API Reference

Mounted under `/api/v1/evaluation`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/evaluation/latest` | Returns the most recent evaluation record from `evaluation_history`. |
| `GET` | `/api/v1/evaluation/history?limit=100&offset=0` | Returns the last 100 evaluation records with complete breakdown payloads. |
| `GET` | `/api/v1/evaluation/summary` | Returns aggregated KPIs, stage latencies, provider comparisons, trend series, and heatmap matrix. |
| `POST` | `/api/v1/evaluation/run` | Executes the automated 50+ query benchmark suite from `evaluation/datasets/`. |
| `GET` | `/api/v1/evaluation/export?format=csv\|json\|pdf` | Exports comprehensive reports (Executive Summary, Metrics, Charts, Provider Breakdown, Version, Timestamp). |

### Example: Run Benchmark
```bash
curl -X POST http://localhost:8000/api/v1/evaluation/run \
  -H "Content-Type: application/json" \
  -d '{"dataset_name": "sample_questions.json", "max_queries": 55, "use_live_llm": false}'
```

### Example: Export PDF Report
```bash
curl -L "http://localhost:8000/api/v1/evaluation/export?format=pdf" -o docmind_eval_report.pdf
```

---

## 5. Benchmark Workflow & Ground Truth Dataset Format

Datasets live under `evaluation/datasets/`:
- `sample_questions.json` (55 curated questions across RAG, ML, DL, CNNs, Optimization, NLP, and DocMind architecture)
- `expected_answers.json` (reference answers)
- `benchmark_config.json` (quality thresholds and overhead budget)

### Question Entry Schema
```json
{
  "id": "q01",
  "question": "What is Retrieval-Augmented Generation?",
  "expected_keywords": ["retrieval", "vector", "LLM", "context"],
  "expected_sources": ["benchmark_corpus.txt", "test_architecture.txt"],
  "expected_topic": "RAG Architecture"
}
```

---

## 6. Evaluation Dashboard (`frontend/src/pages/EvaluationPage.tsx`)

Accessible via `/evaluation` in the sidebar, adhering to the **Jet Black (`#0A0A0A`)**, **Cerulean Blue (`#007BA7`)**, and **Neon Rose (`#FF2D95`)** design system:
- **Overall RAG Health**: Overall RAG Score, Grounding, Retrieval Score, Generation Quality, Hallucination Risk
- **Retrieval & Generation Cards**: Precision@K, Recall@K, MRR, NDCG, Doc Coverage, Diversity, Faithfulness, Citation Coverage, Completeness, Reasoning
- **Performance Telemetry**: Rewrite, Planner, Retrieval, Reranking, Generation, Total Latency, and Token Usage
- **Interactive Recharts Suite**: Line Chart, Area Chart, Bar Chart, Pie Chart, and Query × Quality Heatmap Matrix
- **Evaluation History Table**: Last 100 evaluations with expandable rows inspecting citations, DCG/IDCG/NDCG, stage latencies, and token breakdown
- **One-Click Exports**: Download `CSV`, `JSON`, and `PDF` reports directly from the dashboard header.


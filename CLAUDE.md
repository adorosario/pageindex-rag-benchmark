# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Independent benchmark comparing PageIndex (FAISS-based RAG) against Google Gemini, CustomGPT.ai, and OpenAI RAG on 100 factual questions from SimpleQA-Verified. Results and methodology are published for reproducibility.

**Disclosure**: Author is CEO of CustomGPT.ai (one of the evaluated providers). All data is public.

## Build & Run Commands

```bash
# Build the container
docker compose build

# Run benchmark (100 questions)
docker compose run --rm pageindex python scripts/fair_benchmark.py --limit 100

# Run with verbose output
docker compose run --rm pageindex python scripts/fair_benchmark.py --limit 100 --verbose

# Test the two-stage search pipeline directly
docker compose run --rm pageindex python scripts/two_stage_search.py
```

Results are saved to `runs/fair_benchmark_<timestamp>/` with `results.json` and `detailed_results.jsonl`.

## Prerequisites

- Docker and Docker Compose
- `.env` file with `OPENAI_API_KEY`
- Pre-built FAISS index at `/app/faiss_index/` (index.faiss, metadata.pkl, texts.pkl)
- Pre-built embeddings at `/app/embeddings/embeddings_all.jsonl`

## Architecture

### Two-Stage Retrieval Pipeline (`scripts/two_stage_search.py`)

1. **Vector Search**: Query embedded via `text-embedding-3-small` → FAISS returns top 30 chunks from ~81,868 chunks across 969 documents
2. **Document Scoring**: Chunks grouped by doc_id, scored as `Σ chunk_scores / √n`, top 5 documents selected, context built from top 10 chunks per doc (max 12K chars)

### Benchmark Flow (`scripts/fair_benchmark.py`)

1. Load questions from CSV
2. For each question: retrieve context → generate answer (`gpt-5.1`, temp=0) → judge answer (`gpt-4.1-mini`)
3. Calculate quality score: `(correct - 4 × incorrect) / total`
4. Save results

### Audit Logger (`scripts/audit_logger.py`)

Structured JSONL logging for provider requests, judge evaluations, tree searches, and source downloads. Not wired into `fair_benchmark.py` currently but available for extended tracing.

## Key Constants

| Constant | Value | Location |
|----------|-------|----------|
| Answer model | `gpt-5.1` | `fair_benchmark.py` |
| Judge model | `gpt-4.1-mini` | `fair_benchmark.py` |
| Embedding model | `text-embedding-3-small` | `two_stage_search.py` |
| Penalty ratio | 4.0 | `fair_benchmark.py` |
| Top chunks | 30 | `two_stage_search.py` |
| Top documents | 5 | `two_stage_search.py` |
| Max context chars | 12,000 | `two_stage_search.py` |

## Data Files

- `data/benchmark_questions.csv` — 100 questions (columns: original_index, problem, answer, topic, etc.)
- `data/provider_requests.jsonl` — 400 raw API logs (4 providers × 100 questions)
- `results/fair_benchmark_results.json` — Summary metrics
- `results/detailed_results.jsonl` — Per-question verdicts

## Design Decision

PageIndex's tree-based reasoning was **not used** because building tree indices for 1000 documents would require 33-83 hours of LLM calls. This benchmark tests PageIndex's FAISS fallback path, representing the realistic multi-document scenario.

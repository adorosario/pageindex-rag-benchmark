# PageIndex Fair Multi-Document RAG Benchmark Report

**Date:** January 29, 2026
**Run ID:** 20260129_172234

## Executive Summary

This report presents results from a **fair multi-document comparison** between PageIndex's fallback pipeline and commercial RAG providers on the [SimpleQA-Verified](https://huggingface.co/datasets/google/simpleqa-verified) benchmark (Google DeepMind, [arXiv:2509.07968](https://arxiv.org/abs/2509.07968)).

### Important Note

PageIndex's core technology (tree-based reasoning) was **not used** in this benchmark because building tree indices for ~1000 documents was impractical (2-5 minutes per document via LLM calls). Instead, this benchmark tests what happens when PageIndex falls back to standard FAISS vector retrieval -- which is the realistic scenario for multi-document RAG at scale.

### Results

| Provider | Quality Score | Correct | Incorrect | Not Attempted |
|----------|:------------:|:-------:|:---------:|:-------------:|
| Google Gemini RAG | **0.90** | 98 | 2 | 0 |
| CustomGPT RAG | 0.78 | 86 | 2 | 12 |
| PageIndex (multi-doc) | 0.69 | 81 | 3 | 16 |
| OpenAI RAG | 0.54 | 90 | 9 | 1 |

Quality Score = (correct - 4 x incorrect) / total

## Methodology

### Corpus
- **969 unique documents** indexed in FAISS vector store
- **81,868 chunks** embedded with text-embedding-3-small
- Documents sourced from SimpleQA-Verified source URLs (Google DeepMind benchmark based on OpenAI's SimpleQA)

### Retrieval Pipeline (for PageIndex multi-doc entry)
1. **Embedding**: Query embedded with text-embedding-3-small
2. **FAISS Search**: Top 30 chunks retrieved by cosine similarity
3. **Document Scoring**: Chunks grouped by document, scored with `DocScore = Σ ChunkScore / √n`
4. **Context Building**: Top 5 documents, top 10 chunks per document (max 12,000 chars)
5. **Answer Generation**: GPT-5.1 (temperature=0, max_completion_tokens=200)
6. **Judging**: GPT-4.1-mini using simple-evals grader template

### Same Methodology Across Providers
- **Same 100 questions** from benchmark_questions.csv
- **Same judge model** (GPT-4.1-mini) for all evaluations
- **Same scoring formula** (penalty_ratio=4.0)
- **Same source documents** (~1000 docs scraped from SimpleQA-Verified golden URLs)

### What Differs
- Each provider uses its **own retrieval method** and **own answer model**
- This is an **end-to-end provider comparison**

## Results Analysis

### Accuracy When Attempted
| Provider | Attempted | Accuracy |
|----------|:---------:|:--------:|
| Google Gemini RAG | 100% | 98.0% |
| PageIndex (multi-doc) | 84% | 96.4% |
| CustomGPT RAG | 88% | 97.7% |
| OpenAI RAG | 99% | 90.9% |

When PageIndex does answer, it achieves excellent accuracy (96.4%). The limitation is abstention: 16% of questions were not attempted.

### Abstention Analysis

The 16 NOT_ATTEMPTED results fall into:
- **Retrieval failure (3)**: FAISS search did not surface the correct document
- **Context extraction failure (13)**: Correct document retrieved, but answer not in extracted chunks

### Cost Comparison

| Provider | Estimated Cost per Query |
|----------|:------------------------:|
| Google Gemini RAG | $0.002 |
| PageIndex (multi-doc) | ~$0.01 |
| OpenAI RAG | $0.02 |
| CustomGPT RAG | $0.10 |

## Historical Context

### Previous Run (Jan 26, 2026)
- **Model**: gpt-4.1-mini (NOT gpt-5.1)
- **Quality**: 0.49 (69 correct, 5 incorrect, 26 not attempted)
- **Bug**: `two_stage_search.py` had a data structure mismatch (texts stored as list, accessed as dict)

### Current Run (Jan 29, 2026)
- **Model**: gpt-5.1
- **Quality**: 0.69 (81 correct, 3 incorrect, 16 not attempted)
- **Fix**: Corrected text retrieval to use FAISS index alignment

The improvement from 0.49 to 0.69 is attributable to:
1. Upgrading answer model from gpt-4.1-mini to gpt-5.1
2. Fixing the text retrieval bug in two_stage_search.py

## Data Notes

### Provider Judgment Reproducibility
The `data/provider_requests.jsonl` file contains raw API request/response logs for all 4 providers (400 rows). Judgment verdicts (CORRECT/INCORRECT/NOT_ATTEMPTED) for Google Gemini, CustomGPT, and OpenAI RAG were computed using the same GPT-4.1-mini judge and grading prompt as the PageIndex pipeline. To reproduce these judgments, run the judge prompt from `scripts/fair_benchmark.py` against each provider's response and the expected answer from `data/benchmark_questions.csv`.

PageIndex per-question judgments are included in `results/detailed_results.jsonl`.

### OpenAI_Vanilla Baseline
The `provider_requests.jsonl` file includes an `OpenAI_Vanilla` provider (100 rows, `uses_rag: false`) which is a bare GPT-5.1 baseline with no retrieval. This was collected for reference but is excluded from the main results table because it is not a RAG system. The "OpenAI RAG" entry in the results table corresponds to `OpenAI_RAG` (`uses_rag: true`), which uses GPT-5.1 with the File Search API.

### Error vs. Abstention
All 16 NOT_ATTEMPTED results in the PageIndex run were legitimate abstentions (the model responded with "I don't know" or similar). Zero were caused by API errors or exceptions. This was verified by manual inspection of `results/detailed_results.jsonl`.

## Files

- `results/fair_benchmark_results.json` - Summary metrics
- `results/detailed_results.jsonl` - Per-question details (PageIndex, with verdicts)
- `data/benchmark_questions.csv` - 100 questions used
- `data/provider_requests.jsonl` - All provider API calls (400 rows, raw Q&A, no judgments)

## Disclosure

This benchmark was conducted independently by Alden Do Rosario, CEO of CustomGPT.ai. CustomGPT RAG is one of the evaluated providers. All data is published for transparency.

---

*Generated from fair_benchmark.py run 20260129_172234*

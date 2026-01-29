# PageIndex Fair Multi-Document RAG Benchmark Report

**Date:** January 26, 2026
**Run ID:** 20260126_043117

## Executive Summary

This report presents results from a **fair comparison** between PageIndex and other RAG providers on the SimpleQA benchmark. Unlike previous benchmarks where PageIndex was "spoon-fed" the correct document, this test requires PageIndex to search across **all 1,000 documents** to find relevant information.

### Key Finding

When PageIndex must discover which document is relevant (like other RAG providers do), its quality score drops significantly:

| Provider | Quality Score | Correct | Incorrect | Not Attempted |
|----------|--------------|---------|-----------|---------------|
| Google Gemini RAG | **0.90** | 98 | 2 | 0 |
| PageIndex (spoon-fed)* | 0.89 | 89 | 0 | 11 |
| CustomGPT RAG | 0.78 | 86 | 2 | 12 |
| OpenAI RAG | 0.54 | 90 | 9 | 1 |
| **PageIndex Fair** | **0.49** | **69** | **5** | **26** |

*Previous benchmark where PageIndex was given the correct document

## Methodology

### What Changed: Fair Multi-Document Search

**Previous (Unfair) Approach:**
- For each question, we pre-downloaded the specific URLs listed in SimpleQA
- PageIndex only had to search within 6-8 documents per question
- The correct answer was always in one of those documents

**New (Fair) Approach:**
- All 1,000 documents from SimpleQA were indexed
- FAISS vector search finds relevant documents (no hints)
- Two-stage retrieval pipeline:
  1. Vector search → top 5 documents
  2. Context building → top 3 chunks per document
- Same questions, same judge, same scoring as other providers

### Technical Implementation

1. **Corpus:** 1,000 markdown documents (converted from verified sources)
2. **Embeddings:** OpenAI text-embedding-3-small (102,446 chunks total)
3. **Vector Search:** FAISS IndexFlatIP with cosine similarity
4. **Document Scoring:** PageIndex formula: `DocScore = (1/√(N+1)) × Σ ChunkScore(n)`
5. **Answer Generation:** gpt-4.1-mini with retrieved context
6. **Judge:** gpt-4.1-mini (same as other benchmarks)
7. **Scoring:** Quality Score = (Correct - 4 × Incorrect) / 100

## Results Analysis

### Why the Lower Score?

| Metric | PageIndex Fair | Google Gemini |
|--------|----------------|---------------|
| Correct | 69 | 98 |
| Incorrect | 5 | 2 |
| Not Attempted | **26** | 0 |
| Accuracy (attempted) | 93.24% | 98.0% |

The main issue is the **high abstention rate (26%)**:
- When PageIndex finds and uses the right context, accuracy is excellent (93%)
- But in 26% of cases, the retrieval fails to find useful context
- The model correctly says "I don't know" instead of guessing

### What This Means

1. **Retrieval is the bottleneck**: The two-stage retrieval doesn't always surface the right document from 1,000 options

2. **Accuracy when attempted is good**: 93.24% accuracy shows the PageIndex approach works well when the right document is found

3. **Honest calibration**: High abstention is better than confident wrong answers (only 5 incorrect vs OpenAI RAG's 9)

## Comparison Context

### Provider Architectures

| Provider | Document Count | Retrieval Method |
|----------|----------------|------------------|
| Google Gemini RAG | 1,000+ | Proprietary grounding |
| CustomGPT RAG | 1,000+ | Proprietary retrieval |
| OpenAI RAG | 1,000+ | File Search API |
| **PageIndex Fair** | **1,000** | **FAISS + chunk ranking** |

### Cost Comparison

| Provider | Cost per Request |
|----------|------------------|
| Google Gemini RAG | $0.002 |
| PageIndex Fair | ~$0.01 (embedding + generation) |
| CustomGPT RAG | $0.10 |
| OpenAI RAG | $0.02 |

## Recommendations

### If High Accuracy is Critical

Use Google Gemini RAG (0.90 quality) or CustomGPT RAG (0.78 quality) for production multi-document RAG.

### If PageIndex is Required

For better performance with PageIndex on large document collections:

1. **Improve retrieval**: Consider hybrid search (BM25 + vector) or query expansion
2. **Tune top-k**: Experiment with different chunk retrieval counts
3. **Better chunking**: Semantic chunking instead of fixed character splits
4. **Use PageIndex trees**: Build hierarchical summaries for better document-level understanding

### For Smaller Document Collections

PageIndex excels when:
- Document count is small (10-50 documents)
- Documents can be pre-identified for the query
- Hierarchical tree search can be used per-document

## Files Generated

- `/app/runs/fair_benchmark_20260126_043117/results.json` - Summary metrics
- `/app/runs/fair_benchmark_20260126_043117/detailed_results.jsonl` - Per-question details
- `/app/faiss_index/` - Vector index (102,446 chunks)
- `/app/embeddings/embeddings_all.jsonl` - Raw embeddings

## Conclusion

The fair multi-document benchmark reveals that PageIndex's strength is **within-document search** using hierarchical trees, not **cross-document discovery**. When competing directly with other RAG providers on document retrieval, PageIndex's vector-based approach achieves lower quality scores (0.49 vs 0.54-0.90).

This is an honest assessment. The previous benchmark showing 0.89 quality was misleading because PageIndex was given hints about which document to search.

---

*Generated by fair_benchmark.py on 2026-01-26*

# PageIndex RAG Benchmark

Independent benchmark comparing [PageIndex](https://github.com/VectifyAI/PageIndex) tree-based RAG against Google Gemini, CustomGPT.ai, and OpenAI RAG on [SimpleQA-Verified](https://huggingface.co/datasets/google/simpleqa-verified) (100 factual questions, ~1000 source documents).

## Results

### Fair Multi-Document Comparison

All providers search the same ~1000 documents to answer 100 factual questions. No provider is given hints about which document contains the answer.

| Provider | Quality Score | Correct | Incorrect | Not Attempted |
|----------|:------------:|:-------:|:---------:|:-------------:|
| Google Gemini RAG | **0.90** | 98 | 2 | 0 |
| CustomGPT.ai RAG | 0.78 | 86 | 2 | 12 |
| **PageIndex (multi-doc)*** | **0.69** | 81 | 3 | 16 |
| OpenAI RAG | 0.54 | 90 | 9 | 1 |

**Quality Score** = (correct - 4 x incorrect) / total. The 4x penalty is a design choice that favors precision over recall.

*\*PageIndex tree-based reasoning could not be used in this multi-document benchmark because building tree indices for ~1000 documents was impractical (2-5 min per doc via LLM calls). This tests PageIndex's FAISS vector search fallback + GPT-5.1 answer generation.*

**Note:** These results are based on a 100-question sample from the 1,000-question SimpleQA-Verified benchmark. Rankings should be treated as directional indicators rather than statistically definitive.

### Key Findings

1. **PageIndex multi-doc places 3rd**: Quality score of 0.69, ahead of OpenAI RAG (0.54), behind Google Gemini (0.90) and CustomGPT.ai (0.78).

2. **96.4% accuracy when answering**: Only 3 incorrect answers out of 84 attempted. The pipeline prefers to abstain rather than guess wrong.

3. **Scalability is the core limitation**: PageIndex's strength (tree reasoning) can't scale to multi-document scenarios. Building tree indices for 1000 docs takes 33-83 hours of LLM calls.

4. **PageIndex is designed for single-document QA**: PageIndex's team has noted that it is currently designed for single long document question answering. Its tree-based reasoning excels in that scenario.

## Methodology

### Dataset
- **100 questions** from [SimpleQA-Verified](https://huggingface.co/datasets/google/simpleqa-verified) (factual Q&A with verified source documents)
- **~1000 source documents** indexed in a FAISS vector store (969 unique docs, 81,868 chunks)
- Questions span topics: Science, History, Geography, Sports, Music, Politics, Art, TV shows

### Evaluation Pipeline
- **Retrieval**: FAISS vector search (text-embedding-3-small) -> top 5 documents -> top 10 chunks per doc
- **Answer generation**: GPT-5.1 (temperature=0) with retrieved context
- **Judge**: GPT-4.1-mini using the [simple-evals grader template](https://github.com/openai/simple-evals) (adapted for JSON output)
- **Scoring**: Quality = (correct - 4 x incorrect) / total (penalty_ratio=4.0)

### Comparison Fairness

| Factor | Same across providers? |
|--------|:---------------------:|
| Questions | Yes (same 100) |
| Judge model | Yes (GPT-4.1-mini) |
| Scoring formula | Yes (penalty_ratio=4.0) |
| Source documents | Yes (~1000 docs) |
| Answer model | No (each provider uses its own) |
| Retrieval method | No (each provider uses its own) |

This is an **end-to-end provider comparison**. Each provider uses its native retrieval and generation pipeline. The comparison is fair in that all providers face the same task with the same evaluation.

## Repository Structure

```
pageindex-rag-benchmark/
├── data/
│   ├── benchmark_questions.csv      # 100 questions used
│   └── provider_requests.jsonl      # All provider API calls (400 rows)
├── results/
│   ├── fair_benchmark_results.json  # PageIndex summary metrics
│   └── detailed_results.jsonl       # Per-question PageIndex results
├── scripts/
│   ├── fair_benchmark.py            # Benchmark runner
│   ├── two_stage_search.py          # FAISS + chunk retrieval
│   └── audit_logger.py              # Logging utility
├── docs/
│   └── FAIR_BENCHMARK_REPORT.md     # Full methodology report
├── article/
│   └── medium-article.md            # Medium article source
├── ATTRIBUTION.md                   # Credits to VectifyAI, OpenAI
└── LICENSE                          # Apache 2.0
```

## Reproducibility

### Prerequisites
- Docker and Docker Compose
- OpenAI API key (for embeddings + answer generation + judging)
- ~1000 SimpleQA-Verified source documents indexed in FAISS

### Run the Benchmark
```bash
docker compose run --rm pageindex python scripts/fair_benchmark.py --limit 100
```

Results are saved to `runs/fair_benchmark_<timestamp>/`.

## Context: The PageIndex Approach

[PageIndex](https://github.com/VectifyAI/PageIndex) by VectifyAI is a **tree-based RAG** system. Instead of chunking documents and doing similarity search, it:

1. Builds a hierarchical tree index (like a table of contents)
2. Uses LLM reasoning to navigate the tree and find relevant sections
3. Extracts content from the identified sections

This approach excels at **within-document search** (finding specific information in a known document). VectifyAI's [Mafin 2.5](https://github.com/VectifyAI/Mafin2.5-FinanceBench), powered by PageIndex, achieved 98.7% accuracy on FinanceBench for financial document QA.

However, in a **multi-document scenario** (finding which document among 1000 contains the answer), PageIndex must first do vector retrieval to identify candidate documents -- the same approach as traditional RAG. The tree-based reasoning only helps after the right document is found.

## Disclosure

This benchmark was conducted independently by [Alden Do Rosario](https://github.com/adorosario), CEO of [CustomGPT.ai](https://customgpt.ai). CustomGPT.ai RAG is one of the evaluated providers. All methodology, data, and results are published here for transparency.

## Attribution

- [PageIndex](https://github.com/VectifyAI/PageIndex) by VectifyAI
- [SimpleQA-Verified](https://huggingface.co/datasets/google/simpleqa-verified) by Google DeepMind (based on OpenAI's [SimpleQA](https://github.com/openai/simple-evals))
- See [ATTRIBUTION.md](ATTRIBUTION.md) for full credits

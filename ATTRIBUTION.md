# Attribution

## PageIndex

This benchmark evaluates [PageIndex](https://github.com/VectifyAI/PageIndex) by [VectifyAI](https://vectify.ai).

PageIndex is a reasoning-based RAG system that builds hierarchical tree indices from documents and uses LLMs to reason over that index for agentic, context-aware retrieval. All rights to the original PageIndex code belong to VectifyAI.

- **Repository**: https://github.com/VectifyAI/PageIndex
- **License**: Apache 2.0
- **Website**: https://vectify.ai/pageindex

## SimpleQA-Verified

The benchmark questions are sourced from [SimpleQA](https://github.com/openai/simple-evals) by OpenAI, a factual question-answering benchmark with verified source documents.

- **Repository**: https://github.com/openai/simple-evals
- **Paper**: OpenAI SimpleQA (2025)

## RAG Providers Evaluated

- **Google Gemini RAG**: Gemini-3-Pro with native grounding
- **CustomGPT RAG**: CustomGPT.ai RAG platform (GPT-5.1 via API)
- **OpenAI RAG**: GPT-5.1 with File Search API
- **PageIndex**: Open-source tree-based RAG with FAISS retrieval + GPT-5.1

## Disclosure

This benchmark was conducted independently by [Alden Do Rosario](https://github.com/adorosario), CEO of [CustomGPT.ai](https://customgpt.ai). CustomGPT RAG is one of the evaluated providers. All providers were evaluated using the same methodology, judge model, and scoring formula. Full audit data is included in this repository for reproducibility.

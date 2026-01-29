# No, PageIndex Will Not "Kill" RAG, But It Is Indeed Excellent In Some Cases

*An independent benchmark of tree-based vs. vector-based RAG across 1000 documents*

---

A viral tweet recently claimed that PageIndex, a new open-source "reasoning-based RAG" system, achieved 98.7% accuracy on a financial benchmark without vector databases, chunking, or similarity search. The AI community took notice. Some called it a "RAG killer."

I spent the past week putting that claim to the test with an independent benchmark. The results tell a more nuanced story.

---

## What Is PageIndex?

[PageIndex](https://github.com/VectifyAI/PageIndex) by VectifyAI takes a fundamentally different approach to document retrieval. Instead of the standard chunk-embed-retrieve pipeline, it:

1. Builds a **hierarchical tree index** (like a semantic table of contents)
2. Uses **LLM reasoning** to navigate the tree and find relevant sections
3. Extracts content from identified sections for answer generation

The idea is compelling: similarity search finds *similar* content, but reasoning finds *relevant* content. When a question asks for a certification *date*, similarity search might return a certifications *table* -- related but useless. Tree-based reasoning can navigate to the timeline section instead.

PageIndex's 98.7% accuracy on FinanceBench is real. But FinanceBench tests single-document question answering -- each question targets a specific financial report. The question is: **what happens when PageIndex has to find the right document first?**

---

## The Benchmark: 100 Questions, 1000 Documents

I designed a fair multi-document benchmark:

- **100 factual questions** from [SimpleQA-Verified](https://github.com/openai/simple-evals) (verified source coverage)
- **~1000 source documents** indexed together (no hints about which document contains the answer)
- **Same judge model** (GPT-4.1-mini) across all providers
- **Same scoring** with penalty-aware formula: Quality = (correct - 4 x incorrect) / 100

The 4x penalty for incorrect answers reflects a simple truth: in production, a confident wrong answer is far worse than saying "I don't know."

I evaluated four providers head-to-head:

| Provider | Retrieval Method |
|----------|-----------------|
| Google Gemini RAG | Gemini-3-Pro with native grounding |
| CustomGPT RAG | Proprietary RAG pipeline |
| PageIndex | FAISS vector search + tree reasoning (GPT-5.1) |
| OpenAI RAG | GPT-5.1 with File Search API |

---

## Results

| Provider | Quality Score | Correct | Incorrect | Not Attempted |
|----------|:------------:|:-------:|:---------:|:-------------:|
| Google Gemini RAG | **0.90** | 98 | 2 | 0 |
| CustomGPT RAG | 0.78 | 86 | 2 | 12 |
| **PageIndex** | **0.69** | 81 | 3 | 16 |
| OpenAI RAG | 0.54 | 90 | 9 | 1 |

PageIndex places **third** with a quality score of 0.69 -- ahead of OpenAI RAG but behind Google Gemini and CustomGPT.

---

## Why the Gap?

The answer is straightforward: **PageIndex is designed for single-document question answering, not multi-document retrieval.**

When I shared early results on X (Twitter), PageIndex's official account responded:

> "It is now designed for single long document question answering, for multiple documents (more than 5), we support via other customized techniques."

> "The open-source version currently uses a sequential indexing process, which can be slow for long documents. It's intended more as a proof of concept than an enterprise-ready system."

This is honest and accurate. In a multi-document scenario, PageIndex must first find the right document using vector search -- the same approach every other RAG system uses. The tree-based reasoning only helps *after* the right document is identified.

### Where the 16% Abstention Comes From

PageIndex's 16 "Not Attempted" answers fall into two categories:

1. **Retrieval failure (3 cases)**: The FAISS vector search failed to surface the right document from 1000 options
2. **Context extraction failure (13 cases)**: The right document was retrieved, but the specific fact wasn't in the extracted chunks

When PageIndex can't find sufficient context, it says "I don't know" rather than guessing. This is actually a valuable property -- when it *does* answer, it achieves **96.4% accuracy**.

---

## Where PageIndex Excels

The 98.7% FinanceBench claim isn't misleading -- it's just specific. PageIndex genuinely excels at:

**Single-document deep analysis.** When you point PageIndex at a specific document and ask detailed questions, the tree-based reasoning navigates complex structure (financial reports, legal filings, technical manuals) better than chunk-based similarity search.

**Zero-hallucination tolerance.** In my benchmark, PageIndex had only 3 incorrect answers out of 84 attempted (96.4% accuracy). It prefers abstention over confident errors.

**Structured documents.** Documents with natural hierarchy (sections, subsections, numbered items) play to PageIndex's strengths. The tree index mirrors the document's own structure.

**Auditability.** Every retrieval decision is traceable -- which tree nodes were considered, which were selected, and why. This matters for compliance-heavy domains.

---

## Where PageIndex Struggles

**Multi-document discovery.** Finding the right document among hundreds or thousands requires the same vector search that PageIndex is supposed to replace. The tree reasoning only kicks in after document selection.

**Scale.** Building a tree index takes 2-5 minutes per document (LLM calls). This makes PageIndex impractical for dynamic or large-scale corpora.

**Latency.** At 2.8 seconds per query in my benchmark, PageIndex is competitive but relies on GPT-5.1 for answer generation (same as the comparison).

**Large documents.** Documents with 50+ tree nodes can cause context overflow in tree search.

---

## The Honest Takeaway

PageIndex will not "kill" RAG. Vector-based retrieval remains the practical choice for most applications: it's fast, scalable, and well-understood.

But PageIndex *is* excellent in some cases. For high-stakes, single-document analysis -- legal review, financial due diligence, regulatory compliance -- the combination of structural reasoning and principled abstention is genuinely valuable.

The real future likely involves **hybrid approaches**: vector retrieval for document discovery, tree-based reasoning for precise extraction within top candidates. PageIndex's contribution is demonstrating that LLM reasoning over document structure can outperform similarity search for within-document retrieval.

That's not a RAG killer. But it is a meaningful addition to the toolkit.

---

## Methodology & Reproducibility

Full benchmark code, data, and results are published at:
**[github.com/adorosario/pageindex-rag-benchmark](https://github.com/adorosario/pageindex-rag-benchmark)**

### Technical Details
- **Questions**: 100 from SimpleQA-Verified (factual, single-answer)
- **Documents**: ~1000 indexed in FAISS (text-embedding-3-small, 81,868 chunks)
- **Answer model**: GPT-5.1 (temperature=0) for PageIndex; each provider uses its native model
- **Judge**: GPT-4.1-mini using the simple-evals grader template
- **Scoring**: Quality = (correct - 4 x incorrect) / total (penalty_ratio=4.0)

### Disclosure
I am the CEO of [CustomGPT.ai](https://customgpt.ai), one of the evaluated providers. All providers were evaluated using the same methodology and scoring. Full audit data is published for transparency.

---

*Alden Do Rosario is CEO of [CustomGPT.ai](https://customgpt.ai). The full benchmark code and results are available at [github.com/adorosario/pageindex-rag-benchmark](https://github.com/adorosario/pageindex-rag-benchmark).*

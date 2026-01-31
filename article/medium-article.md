# No, PageIndex Will Not "Kill" RAG, But It Is Indeed Excellent In Some Cases

*An independent benchmark revealing when tree-based RAG outperforms vector RAG -- and when it can't even be used*

---

A [viral tweet from Avi Chawla](https://x.com/_avichawla/status/1882365488498393262) recently claimed that a new RAG approach "does not need a vector DB, does not embed data, involves no chunking, performs no similarity search — and it hit 98.7% accuracy on a financial benchmark (SOTA)." The system in question: [PageIndex](https://github.com/VectifyAI/PageIndex), an open-source "reasoning-based RAG" by VectifyAI. The AI community took notice. Some called it a "RAG killer."

I spent the past week trying to benchmark PageIndex against leading RAG providers. The results tell a more nuanced story -- and reveal a fundamental limitation that no one is talking about.

---

## What Is PageIndex?

[PageIndex](https://github.com/VectifyAI/PageIndex) by VectifyAI takes a fundamentally different approach to document retrieval. Instead of the standard chunk-embed-retrieve pipeline, it:

1. Builds a **hierarchical tree index** (like a semantic table of contents)
2. Uses **LLM reasoning** to navigate the tree and find relevant sections
3. Extracts content from identified sections for answer generation

The idea is compelling: similarity search finds *similar* content, but reasoning finds *relevant* content. 

When a question asks for a certification *date*, similarity search might return a certifications *table* -- related but useless. Tree-based reasoning can navigate to the timeline section instead.

VectifyAI's Mafin 2.5, powered by PageIndex, [achieved 98.7% accuracy on FinanceBench](https://github.com/VectifyAI/Mafin2.5-FinanceBench). But FinanceBench tests single-document question answering -- each question targets a specific financial report. 

The question is: **what happens when you have 1000 documents?**

---

## The Scalability Problem

Here's what I confirmed through testing: **PageIndex's tree-based approach cannot practically scale to multi-document scenarios.**

It's great for single-document use cases (for example: Financial documents), but falls short on large multi-document knowledgebases. 

In our testing using Google's simpleqa-verified dataset (a 1000-question benchmark dataset that has about 2795 documents ), building the index ran into major scalability problems. 

Due to which: We had to fall back to standard vector search -- the same approach it claims to replace.

PageIndex's team has been transparent about this. In a [public exchange](https://x.com/PageIndexAI/status/2016913668114698341?s=20) on X (Twitter), their official account noted that PageIndex is currently designed for single long document question answering, and that for multiple documents (more than 5), they support via other customized techniques. 

They also acknowledged that the open-source version uses a sequential indexing process intended more as a proof of concept than an enterprise-ready system.

---

## The Benchmark: 100 Questions, 1000 Documents

To evaluate PageIndex in a multi-document scenario, I tested what actually happens at scale: FAISS vector retrieval (the fallback when tree indices aren't available) followed by GPT-5.1 answer generation.

I compared this against three commercial RAG providers, all answering the same 100 questions from [SimpleQA-Verified](https://huggingface.co/datasets/google/simpleqa-verified) across ~1000 source documents:

| Provider | Retrieval Method |
|----------|-----------------|
| Google Gemini RAG | Gemini 3 Pro with native grounding |
| CustomGPT.ai RAG | Proprietary RAG pipeline |
| PageIndex (multi-doc) | FAISS vector search + GPT-5.1 |
| OpenAI RAG | GPT-5.1 with File Search API |

### Scoring

Quality = (correct - 4 x incorrect) / total

The 4x penalty for incorrect answers reflects a design choice that favors precision over recall: a confident wrong answer costs four times as much as a correct answer earns. 

This benefits conservative systems that abstain when uncertain. With a different penalty ratio, rankings would change.

---

## Results

| Provider | Quality Score | Correct | Incorrect | Not Attempted |
|----------|:------------:|:-------:|:---------:|:-------------:|
| Google Gemini RAG | **0.90** | 98 | 2 | 0 |
| CustomGPT.ai RAG | 0.78 | 86 | 2 | 12 |
| PageIndex (multi-doc) | 0.69 | 81 | 3 | 16 |
| OpenAI RAG | 0.54 | 90 | 9 | 1 |

**Note:** These results are based on a 100-question sample from SimpleQA-Verified, not the full 1,000-question benchmark. With this sample size, the rankings should be treated as directional indicators rather than statistically definitive. The difference between adjacent providers (e.g., CustomGPT.ai at 0.78 vs PageIndex at 0.69) may not be statistically significant at n=100.

PageIndex's multi-document fallback places **third** with a quality score of 0.69 -- ahead of OpenAI RAG but behind Google Gemini and CustomGPT.ai.

The 16 "Not Attempted" answers break down into:

1. **Retrieval failure (3 cases)**: Vector search failed to surface the right document from 1000 options
2. **Context extraction failure (13 cases)**: The right document was retrieved, but the specific fact wasn't in the top chunks

When the pipeline does answer, it achieves **96.4% accuracy** (81 out of 84 attempted).

---

## The Core Trade-off

These results reveal a fundamental trade-off in PageIndex's design:

### Single-Document: Designed to Excel

PageIndex is built for single-document deep analysis. When it can use tree-based reasoning on a known document, the structural navigation genuinely finds information that similarity search misses. PageIndex's own FinanceBench results demonstrate this capability.

### Multi-Document: Falls Back to Standard RAG

When PageIndex faces hundreds or thousands of documents, it can't build tree indices fast enough. It falls back to FAISS vector search -- and performs like any other vector RAG system, without the structural reasoning that makes it special.

This is the core insight: **PageIndex's strength (tree reasoning) is exactly the thing that can't scale.**

---

## Where PageIndex Genuinely Excels

Despite the multi-document limitations, PageIndex's approach has real value:

**Single-document deep analysis.** For financial reports, legal filings, technical manuals -- any scenario where you know which document to search -- tree-based reasoning navigates complex structure better than chunk-based similarity search.

**Structured documents.** Documents with natural hierarchy (sections, subsections, numbered items) play to PageIndex's strengths. The tree index mirrors the document's own structure.

**Auditability.** Every retrieval decision is traceable -- which tree nodes were considered, which were selected, and why. This matters for compliance-heavy domains.

**Principled abstention.** PageIndex says "I don't know" rather than guessing wrong -- a valuable property for high-stakes applications.

---

## The Honest Takeaway

PageIndex will not "kill" RAG. Its core technology (tree reasoning) can't scale to the multi-document retrieval scenarios where most RAG systems operate.

But PageIndex *is* excellent in some cases. For high-stakes, single-document analysis -- legal review, financial due diligence, regulatory compliance -- the combination of structural reasoning and principled abstention is genuinely valuable.

The real future likely involves **hybrid approaches**: vector retrieval for document discovery, tree-based reasoning for precise extraction within top candidates. PageIndex has demonstrated that LLM reasoning over document structure can outperform similarity search for within-document retrieval. That's a meaningful contribution.

Not a RAG killer. But a valuable tool for specific, high-stakes use cases.

---

## Methodology & Reproducibility

Full benchmark code, data, and results are published at:
**[github.com/adorosario/pageindex-rag-benchmark](https://github.com/adorosario/pageindex-rag-benchmark)**

### Technical Details
- **Questions**: 100 from [SimpleQA-Verified](https://huggingface.co/datasets/google/simpleqa-verified) (factual, single-answer)
- **Documents**: ~1000 indexed in FAISS (text-embedding-3-small, 81,868 chunks)
- **Answer model**: GPT-5.1 (temperature=0) for PageIndex fallback pipeline; each commercial provider uses its native model
- **Judge**: GPT-4.1-mini using the [simple-evals grader template](https://github.com/openai/simple-evals)
- **Scoring**: Quality = (correct - 4 x incorrect) / total (penalty_ratio=4.0)
- **Note**: The 4x penalty ratio is a design choice that favors precision-oriented systems. Rankings change under different penalty ratios:

At 1x penalty (no extra punishment for wrong answers), OpenAI RAG (0.81) would rank 3rd ahead of PageIndex (0.78).

### Limitations
- **Sample size**: This benchmark uses 100 questions from the 1,000-question SimpleQA-Verified dataset. Results are directional indicators, not statistically definitive -- differences between adjacent providers may not be significant at this sample size
- **Each provider uses its own answer model**, making this an end-to-end provider comparison rather than a retrieval-only comparison
- **I designed the benchmark methodology** and selected the providers, scoring formula, and penalty ratio using techniques from OpenAI's recent "Why LLMs Hallucinate" paper [https://arxiv.org/abs/2509.04664](https://arxiv.org/abs/2509.04664) -- PS: Read the [blog post](https://openai.com/index/why-language-models-hallucinate/), its a must-read. 

### Disclosure
I am the Founder of [CustomGPT.ai](https://customgpt.ai), one of the evaluated providers. I selected the providers, designed the benchmark methodology, and ran all evaluations. Full audit data is published for transparency so readers can verify the results independently.

---

*Alden Do Rosario is Founder of [CustomGPT.ai](https://customgpt.ai). The full benchmark code and results are available at [github.com/adorosario/pageindex-rag-benchmark](https://github.com/adorosario/pageindex-rag-benchmark).*

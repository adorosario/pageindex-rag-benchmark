#!/usr/bin/env python3
"""
Two-stage retrieval pipeline for fair multi-document RAG benchmark.

Stage 1: Vector search (FAISS) to find top-k relevant documents
Stage 2: Retrieve best chunks from those documents for context

This replicates what other RAG providers do (Gemini, CustomGPT, OpenAI RAG).
"""

import json
import pickle
import sys
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from openai import OpenAI

INDEX_DIR = Path("/app/faiss_index")
EMBEDDINGS_FILE = Path("/app/embeddings/embeddings_all.jsonl")
EMBEDDING_MODEL = "text-embedding-3-small"


class TwoStageSearch:
    def __init__(
        self,
        index_dir: Path = INDEX_DIR,
        embeddings_file: Path = EMBEDDINGS_FILE,
        verbose: bool = True
    ):
        self.client = OpenAI()
        self.index_dir = index_dir
        self.embeddings_file = embeddings_file
        self.verbose = verbose
        self.index = None
        self.metadata = []
        self.texts = []  # List of texts, aligned with FAISS index
        self._load()

    def _load(self):
        """Load FAISS index, metadata, and texts."""
        if self.verbose:
            print("Loading FAISS index...", file=sys.stderr)

        index_file = self.index_dir / "index.faiss"
        self.index = faiss.read_index(str(index_file))

        metadata_file = self.index_dir / "metadata.pkl"
        with open(metadata_file, "rb") as f:
            self.metadata = pickle.load(f)

        texts_file = self.index_dir / "texts.pkl"
        with open(texts_file, "rb") as f:
            self.texts = pickle.load(f)

        if self.verbose:
            n_vectors = self.index.ntotal
            n_texts = len(self.texts)
            print(f"Index loaded: {n_vectors:,} vectors, {n_texts:,} texts", file=sys.stderr)

    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Get embedding for query."""
        response = self.client.embeddings.create(
            input=[query],
            model=EMBEDDING_MODEL
        )
        emb = np.array(response.data[0].embedding, dtype=np.float32)
        return emb / np.linalg.norm(emb)

    def _get_text_by_index(self, idx: int) -> str:
        """Get text for a specific FAISS index."""
        if 0 <= idx < len(self.texts):
            return self.texts[idx]
        return ""

    def search(
        self,
        query: str,
        top_k_chunks: int = 30,
        top_docs: int = 5,
        max_context_chars: int = 12000
    ) -> dict:
        """
        Two-stage search:
        1. Find top chunks via FAISS
        2. Group by document, score documents
        3. Build context from top documents

        Returns dict with doc_ids, context, and metadata.
        """
        # Stage 1: Vector search for top chunks
        query_emb = self._get_query_embedding(query).reshape(1, -1)
        scores, indices = self.index.search(query_emb, top_k_chunks)

        # Group chunks by document, store the FAISS index for later text retrieval
        doc_chunks = {}
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            meta = self.metadata[idx]
            doc_id = meta["doc_id"]
            chunk_index = meta["chunk_index"]
            if doc_id not in doc_chunks:
                doc_chunks[doc_id] = []
            doc_chunks[doc_id].append({
                "chunk_index": chunk_index,
                "faiss_index": idx,  # Store FAISS index for text retrieval
                "score": float(score),
            })

        # Score documents: sum of chunk scores weighted by sqrt(n)
        doc_scores = []
        for doc_id, chunks in doc_chunks.items():
            n = len(chunks)
            doc_score = sum(c["score"] for c in chunks) / (n ** 0.5)
            doc_scores.append({
                "doc_id": doc_id,
                "score": doc_score,
                "matching_chunks": sorted(chunks, key=lambda x: -x["score"]),
            })

        # Sort by document score
        doc_scores.sort(key=lambda x: -x["score"])
        top_doc_scores = doc_scores[:top_docs]

        # Stage 2: Build context from top documents
        context_parts = []
        total_chars = 0

        for doc in top_doc_scores:
            doc_id = doc["doc_id"]

            # Get the best matching chunks (use FAISS index for text retrieval)
            best_chunks = doc["matching_chunks"][:10]

            # Build document context with best chunks
            doc_context = "\n--- Document: " + doc_id + " ---\n"
            for chunk in best_chunks:
                faiss_idx = chunk["faiss_index"]
                chunk_text = self._get_text_by_index(faiss_idx)
                if chunk_text:
                    if total_chars + len(chunk_text) + len(doc_context) < max_context_chars:
                        doc_context += "\n" + chunk_text + "\n"
                        total_chars += len(chunk_text)
                    else:
                        break

            header_len = len("\n--- Document: " + doc_id + " ---\n")
            if len(doc_context) > header_len:
                context_parts.append(doc_context)

            if total_chars >= max_context_chars:
                break

        full_context = "\n".join(context_parts)

        return {
            "context": full_context,
            "top_documents": [d["doc_id"] for d in top_doc_scores],
            "document_scores": [{
                "doc_id": d["doc_id"],
                "score": d["score"],
                "num_matching_chunks": len(d["matching_chunks"]),
            } for d in top_doc_scores],
            "context_chars": len(full_context),
        }


def main():
    """Test two-stage search."""
    print("Initializing two-stage search...")
    search = TwoStageSearch()

    queries = [
        "Who was the first person to walk on the moon?",
        "What is the capital of France?",
        "When was the Eiffel Tower built?",
    ]

    for query in queries:
        print("\n" + "=" * 70)
        print("Query: " + query)
        print("=" * 70)

        result = search.search(query, top_k_chunks=30, top_docs=5)

        print("\nTop documents:")
        for doc in result["document_scores"]:
            doc_id = doc["doc_id"]
            score = doc["score"]
            chunks = doc["num_matching_chunks"]
            print(f"  - {doc_id}: score={score:.4f}, chunks={chunks}")

        context_chars = result["context_chars"]
        print(f"\nContext length: {context_chars} chars")
        print("\nContext preview:")
        print(result["context"][:500] + "...")


if __name__ == "__main__":
    main()

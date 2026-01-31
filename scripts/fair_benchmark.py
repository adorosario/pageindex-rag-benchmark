#!/usr/bin/env python3
"""
Fair multi-document RAG benchmark for PageIndex.

Uses two-stage retrieval:
1. FAISS vector search to find relevant documents (from 1000 docs)
2. Chunk-based context building
3. Answer generation with gpt-5.1

Same methodology as other RAG providers in the benchmark.
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from two_stage_search import TwoStageSearch

# Configuration
QUESTIONS_FILE = Path("/app/data/benchmark_questions.csv")  # Same 100 questions as other benchmark
OUTPUT_DIR = Path("/app/runs")
ANSWER_MODEL = "gpt-5.1"  # Same model as CustomGPT.ai/OpenAI RAG benchmarks
JUDGE_MODEL = "gpt-4.1-mini"  # Same judge
PENALTY_RATIO = 4.0


def load_questions(file_path: Path, limit: int = 100) -> list[dict]:
    """Load questions from CSV."""
    questions = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break
            questions.append({
                "index": i,
                "question": row["problem"],
                "expected_answer": row["answer"],
                "topic": row.get("metadata", ""),
            })
    return questions


def generate_answer(client: OpenAI, question: str, context: str) -> tuple[str, dict]:
    """Generate answer using retrieved context."""
    system_prompt = """You are a helpful assistant that answers questions based on the provided context.
If the context doesn't contain enough information to answer confidently, say "I don't know" or "I'm not sure".
Be concise and factual. Only use information from the provided context."""

    user_prompt = f"""Context:
{context}

Question: {question}

Answer the question based only on the context above. If the answer isn't in the context, say "I don't know"."""

    start_time = time.time()
    response = client.chat.completions.create(
        model=ANSWER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_completion_tokens=200,  # gpt-5.1 uses max_completion_tokens
        temperature=0,
    )
    latency = (time.time() - start_time) * 1000

    answer = response.choices[0].message.content.strip()
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
        "latency_ms": latency,
    }

    return answer, usage


def judge_answer(client: OpenAI, question: str, expected: str, actual: str) -> dict:
    """Judge answer correctness using same methodology as benchmark."""
    system_prompt = """You are evaluating if an answer is correct compared to a reference answer.
Return a JSON object with:
- "verdict": "CORRECT" if the answer matches the expected meaning, "INCORRECT" if wrong, "NOT_ATTEMPTED" if the answer is "I don't know" or similar
- "confidence": a float 0-1 indicating your confidence
- "explanation": brief reason for verdict"""

    user_prompt = f"""Question: {question}

Expected Answer: {expected}

Actual Answer: {actual}

Evaluate if the actual answer is correct. Return JSON only."""

    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},  # Reliable JSON output
        max_tokens=200,
        temperature=0,
    )

    content = response.choices[0].message.content.strip()
    result = json.loads(content)

    # Ensure verdict is uppercase
    if "verdict" in result:
        result["verdict"] = result["verdict"].upper()

    return result


def run_benchmark(num_questions: int = 100, verbose: bool = True):
    """Run the fair benchmark."""
    print("=" * 70)
    print("PageIndex Fair Multi-Document RAG Benchmark")
    print("=" * 70)
    print(f"Answer Model: {ANSWER_MODEL}")
    print(f"Judge Model: {JUDGE_MODEL}")
    print(f"Questions: {num_questions}")
    print(f"Penalty Ratio: {PENALTY_RATIO}")
    print("=" * 70)
    sys.stdout.flush()

    # Initialize
    client = OpenAI()
    search = TwoStageSearch(verbose=verbose)

    # Create output directory
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"fair_benchmark_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Load questions
    print(f"\nLoading questions from {QUESTIONS_FILE}...")
    questions = load_questions(QUESTIONS_FILE, num_questions)
    print(f"Loaded {len(questions)} questions")
    sys.stdout.flush()

    # Run benchmark
    results = []
    n_correct = 0
    n_incorrect = 0
    n_not_attempted = 0
    total_latency = 0
    total_tokens = 0

    start_time = time.time()

    for i, q in enumerate(questions):
        # Progress
        if (i + 1) % 10 == 0 or i == 0:
            print(f"\n--- Question {i + 1}/{len(questions)} ---")
            sys.stdout.flush()

        try:
            # Stage 1 & 2: Retrieve context
            search_result = search.search(
                q["question"],
                top_k_chunks=30,
                top_docs=5,
                max_context_chars=12000
            )

            # Generate answer
            answer, usage = generate_answer(client, q["question"], search_result["context"])
            total_latency += usage["latency_ms"]
            total_tokens += usage["total_tokens"]

            # Judge answer
            judgment = judge_answer(client, q["question"], q["expected_answer"], answer)

            # Update counts
            verdict = judgment.get("verdict", "INCORRECT").upper()
            if verdict == "CORRECT":
                n_correct += 1
            elif verdict == "NOT_ATTEMPTED":
                n_not_attempted += 1
            else:
                n_incorrect += 1

            # Store result
            results.append({
                "index": q["index"],
                "question": q["question"],
                "expected_answer": q["expected_answer"],
                "actual_answer": answer,
                "verdict": verdict,
                "confidence": judgment.get("confidence", 0),
                "explanation": judgment.get("explanation", ""),
                "top_documents": search_result["top_documents"],
                "document_scores": search_result["document_scores"],
                "context_chars": search_result["context_chars"],
                "latency_ms": usage["latency_ms"],
                "tokens": usage["total_tokens"],
            })

            # Progress update
            if (i + 1) % 10 == 0:
                quality = (n_correct - PENALTY_RATIO * n_incorrect) / (i + 1) * 100
                print(f"  Progress: C={n_correct}, I={n_incorrect}, N={n_not_attempted}, Q={quality:.1f}")
                sys.stdout.flush()

        except Exception as e:
            print(f"  Error on question {i}: {e}")
            sys.stdout.flush()
            results.append({
                "index": q["index"],
                "question": q["question"],
                "expected_answer": q["expected_answer"],
                "actual_answer": f"ERROR: {e}",
                "verdict": "NOT_ATTEMPTED",
                "error": str(e),
            })
            n_not_attempted += 1

    elapsed = time.time() - start_time

    # Calculate metrics
    quality_score = (n_correct - PENALTY_RATIO * n_incorrect) / len(questions)
    volume_score = n_correct / len(questions)
    attempted_rate = (n_correct + n_incorrect) / len(questions)
    accuracy_given_attempted = n_correct / (n_correct + n_incorrect) if (n_correct + n_incorrect) > 0 else 0

    # Summary
    summary = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "model": ANSWER_MODEL,
        "questions": len(questions),
        "metrics": {
            "quality_score": quality_score,
            "volume_score": volume_score,
            "attempted_rate": attempted_rate,
            "accuracy_given_attempted": accuracy_given_attempted,
            "n_correct": n_correct,
            "n_incorrect": n_incorrect,
            "n_not_attempted": n_not_attempted,
            "penalty_ratio": PENALTY_RATIO,
            "avg_latency_ms": total_latency / len(questions),
            "avg_tokens": total_tokens / len(questions),
            "total_time_s": elapsed,
        },
    }

    # Save results
    with open(run_dir / "results.json", "w") as f:
        json.dump(summary, f, indent=2)

    with open(run_dir / "detailed_results.jsonl", "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # Print summary
    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)
    print(f"Run ID: {run_id}")
    print(f"Output: {run_dir}")
    print(f"\nResults:")
    print(f"  Correct:       {n_correct}")
    print(f"  Incorrect:     {n_incorrect}")
    print(f"  Not Attempted: {n_not_attempted}")
    print(f"\nMetrics:")
    print(f"  Quality Score: {quality_score:.2f}")
    print(f"  Volume Score:  {volume_score:.2f}")
    print(f"  Accuracy:      {accuracy_given_attempted:.2%}")
    print(f"\nTime: {elapsed:.1f}s")
    print("=" * 70)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fair multi-document RAG benchmark")
    parser.add_argument("--limit", type=int, default=100, help="Number of questions to run")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    run_benchmark(num_questions=args.limit, verbose=args.verbose)

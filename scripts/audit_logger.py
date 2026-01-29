"""
Comprehensive Audit Logging System for PageIndex Benchmark
Ported from simple-evals with RAG-specific extensions for tree search tracing.

Creates per-run directories with full traceability for debugging and analysis.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class AuditLogger:
    """
    Comprehensive audit logger for PageIndex RAG benchmark.
    Provides complete traceability for debugging retrieval and grading.
    """

    def __init__(self, run_id: str = None, output_dir: str = "runs"):
        if run_id is None:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.run_id = run_id
        self.output_dir = Path(output_dir)
        self.run_dir = self.output_dir / f"run_{run_id}"
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Log files for different event types
        self.provider_log_file = self.run_dir / "provider_requests.jsonl"
        self.judge_log_file = self.run_dir / "judge_evaluations.jsonl"
        self.tree_search_log_file = self.run_dir / "tree_searches.jsonl"
        self.source_download_log_file = self.run_dir / "source_downloads.jsonl"
        self.meta_log_file = self.run_dir / "run_metadata.json"

        # Initialize run metadata
        self.run_metadata = {
            "run_id": run_id,
            "start_time": datetime.utcnow().isoformat(),
            "config": {},
            "total_questions": 0,
            "completed_questions": 0,
            "errors": [],
            "metrics": {},
        }

        self._save_metadata()

    def set_config(self, config: Dict[str, Any]):
        """Set run configuration."""
        self.run_metadata["config"] = config
        self._save_metadata()

    def log_provider_request(
        self,
        question_id: str,
        call_type: str,  # "tree_search", "answer_generation", "judge"
        model: str,
        prompt: str,
        response: str,
        latency_ms: float,
        input_tokens: int = None,
        output_tokens: int = None,
        cost_usd: float = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log an LLM API call with complete context."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": self.run_id,
            "question_id": question_id,
            "call_type": call_type,
            "model": model,
            "request": {
                "prompt": prompt,
                "prompt_length": len(prompt),
            },
            "response": {
                "content": response,
                "content_length": len(response),
            },
            "performance": {
                "latency_ms": latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost_usd,
            },
            "metadata": metadata or {},
        }

        self._append_jsonl(self.provider_log_file, log_entry)

    def log_tree_search(
        self,
        question_id: str,
        tree_file: str,
        question: str,
        prompt: str,
        response_raw: str,
        selected_nodes: List[str],
        available_nodes: List[Dict[str, str]],  # [{node_id, title, summary}]
        latency_ms: float,
        input_tokens: int = None,
        output_tokens: int = None,
        thinking: str = None,  # For reasoning models
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log a tree search decision for RAG debugging."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": self.run_id,
            "question_id": question_id,
            "tree_file": tree_file,
            "question": question,
            "search": {
                "prompt": prompt,
                "response_raw": response_raw,
                "thinking": thinking,
                "selected_nodes": selected_nodes,
            },
            "tree_context": {
                "available_nodes": available_nodes,
                "total_nodes": len(available_nodes),
            },
            "performance": {
                "latency_ms": latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            "metadata": metadata or {},
        }

        self._append_jsonl(self.tree_search_log_file, log_entry)

    def log_judge_evaluation(
        self,
        question_id: str,
        question: str,
        target_answer: str,
        predicted_answer: str,
        judge_prompt: str,
        judge_response: str,
        grade_letter: str,  # A, B, C
        grade_string: str,  # CORRECT, INCORRECT, NOT_ATTEMPTED
        reasoning: str,
        latency_ms: float,
        confidence: float = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log LLM-as-judge evaluation with full explanation."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": self.run_id,
            "question_id": question_id,
            "question": question,
            "answers": {
                "target": target_answer,
                "predicted": predicted_answer,
            },
            "judge": {
                "prompt": judge_prompt,
                "response": judge_response,
                "grade_letter": grade_letter,
                "grade_string": grade_string,
                "reasoning": reasoning,
                "confidence": confidence,
                "latency_ms": latency_ms,
            },
            "metadata": metadata or {},
        }

        self._append_jsonl(self.judge_log_file, log_entry)

    def log_source_download(
        self,
        question_id: str,
        url: str,
        success: bool,
        content_length: int,
        method: str,  # "direct", "scrapingbee"
        latency_ms: float,
        error: str = None,
        retry_attempted: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log source download attempts for debugging failed retrievals."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": self.run_id,
            "question_id": question_id,
            "url": url,
            "download": {
                "success": success,
                "content_length": content_length,
                "method": method,
                "latency_ms": latency_ms,
                "error": error,
                "retry_attempted": retry_attempted,
            },
            "metadata": metadata or {},
        }

        self._append_jsonl(self.source_download_log_file, log_entry)

    def log_error(self, component: str, error: str, context: Dict[str, Any] = None):
        """Log errors with context."""
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "component": component,
            "error": str(error),
            "context": context or {},
        }

        self.run_metadata["errors"].append(error_entry)
        self._save_metadata()

    def update_progress(self, completed: int, total: int = None):
        """Update run progress."""
        if total is not None:
            self.run_metadata["total_questions"] = total
        self.run_metadata["completed_questions"] = completed
        self._save_metadata()

    def finalize_run(
        self,
        metrics: Dict[str, Any],
        results: List[Dict[str, Any]] = None,
    ):
        """Finalize the run with summary metrics."""
        self.run_metadata.update({
            "end_time": datetime.utcnow().isoformat(),
            "status": "completed",
            "metrics": metrics,
        })

        if results:
            # Save detailed results separately
            results_file = self.run_dir / "results.json"
            with open(results_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

        self._save_metadata()

    def get_run_summary(self) -> Dict[str, Any]:
        """Get a summary of the current run."""
        return {
            "run_id": self.run_id,
            "run_dir": str(self.run_dir),
            "progress": f"{self.run_metadata['completed_questions']}/{self.run_metadata['total_questions']}",
            "logs": {
                "provider_requests": str(self.provider_log_file),
                "judge_evaluations": str(self.judge_log_file),
                "tree_searches": str(self.tree_search_log_file),
                "source_downloads": str(self.source_download_log_file),
                "metadata": str(self.meta_log_file),
            },
        }

    def _save_metadata(self):
        """Save run metadata to file."""
        with open(self.meta_log_file, "w", encoding="utf-8") as f:
            json.dump(self.run_metadata, f, indent=2, ensure_ascii=False)

    def _append_jsonl(self, filepath: Path, entry: Dict[str, Any]):
        """Append a JSON entry to a JSONL file."""
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def create_run_id() -> str:
    """Create a unique run ID based on timestamp."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_audit_logs(run_id: str, output_dir: str = "runs") -> Dict[str, Any]:
    """Load audit logs for a specific run."""
    run_dir = Path(output_dir) / f"run_{run_id}"

    if not run_dir.exists():
        raise ValueError(f"Run directory not found: {run_dir}")

    logs = {}

    # Load each log file
    log_files = {
        "provider_requests": "provider_requests.jsonl",
        "judge_evaluations": "judge_evaluations.jsonl",
        "tree_searches": "tree_searches.jsonl",
        "source_downloads": "source_downloads.jsonl",
    }

    for key, filename in log_files.items():
        filepath = run_dir / filename
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                logs[key] = [json.loads(line) for line in f if line.strip()]

    # Load metadata
    meta_file = run_dir / "run_metadata.json"
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            logs["metadata"] = json.load(f)

    # Load results if exists
    results_file = run_dir / "results.json"
    if results_file.exists():
        with open(results_file, "r", encoding="utf-8") as f:
            logs["results"] = json.load(f)

    return logs

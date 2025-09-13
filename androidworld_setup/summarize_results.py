#!/usr/bin/env python3
"""Summarize result.txt scores in a results directory.

For each task subfolder under results/, reads result.txt (0/1) if present
and prints a concise summary plus overall success rate.
"""

import argparse
import json
import os
from typing import Dict, List, Optional, Tuple


def read_result_score(task_dir: str) -> Optional[int]:
    """Reads result.txt in task_dir, returning 0/1 or None if missing/invalid."""
    result_path = os.path.join(task_dir, "result.txt")
    if not os.path.isfile(result_path):
        return None
    try:
        with open(result_path, "r") as f:
            content = f.read().strip()
        return int(content)
    except Exception:
        return None


def collect_results(results_dir: str) -> List[Tuple[str, Optional[int]]]:
    """Returns list of (task_name, score)."""
    if not os.path.isdir(results_dir):
        return []
    entries = []
    for name in sorted(os.listdir(results_dir)):
        task_path = os.path.join(results_dir, name)
        if not os.path.isdir(task_path):
            continue
        score = read_result_score(task_path)
        entries.append((name, score))
    return entries


def print_plain(results: List[Tuple[str, Optional[int]]], base_dir: str) -> None:
    successes = 0
    completed = 0
    for _, score in results:
        if score is None:
            continue
        completed += 1
        successes += 1 if score == 1 else 0
    print(f"Score: {successes}/{completed}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect result.txt scores.")
    parser.add_argument(
        "--results_dir",
        default="results",
        help="Base results directory containing per-task folders (default: results)",
    )
    args = parser.parse_args()

    results = collect_results(args.results_dir)
    print_plain(results, args.results_dir)


if __name__ == "__main__":
    main()



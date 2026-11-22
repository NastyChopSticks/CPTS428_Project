#!/usr/bin/env python3
"""Summarize prompt-injection outcomes by condition, model, and vector.

Usage:
    python analyze_injection_results.py path/to/results.csv
    python analyze_injection_results.py path/to/results.csv --output summary.csv

Only completed trials with an explicitly scored (0/1) outcome contribute to
that outcome's scored-trial success rate. Blank outcomes are NOT assumed 0.
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

REQUIRED = {"condition", "model", "vector", "execution_status", "true_success", "partial_success"}
METRICS = ("true_success", "partial_success")
OUTPUT_FIELDS = [
    "condition", "model", "vector", "total_trials", "completed", "failed", "timeout",
    "interrupted", "other_status", "completion_rate_pct",
    "true_success_count", "true_success_scored", "true_success_rate_pct",
    "partial_success_count", "partial_success_scored", "partial_success_rate_pct",
]


def as_binary(value, *, field, row_number):
    s = (value or "").strip()
    if not s:
        return None
    if s in ("0", "1"):
        return int(s)
    raise ValueError(f"Row {row_number}: {field} must be 0, 1, or blank; got {s!r}")


def pct(numerator, denominator):
    return f"{100 * numerator / denominator:.2f}" if denominator else "N/A"


def analyze(path):
    groups = defaultdict(list)
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header")
        missing = REQUIRED - set(reader.fieldnames)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
        for row_number, row in enumerate(reader, start=2):
            if not any((value or "").strip() for value in row.values() if isinstance(value, str)):
                continue
            condition = (row["condition"] or "").strip() or "(unspecified)"
            model = (row["model"] or "").strip() or "(unspecified)"
            vector = (row["vector"] or "").strip() or "(unspecified)"
            status = (row["execution_status"] or "").strip().lower()
            scores = {metric: as_binary(row[metric], field=metric, row_number=row_number)
                      for metric in METRICS}
            groups[(condition, model, vector)].append((status, scores))

    output = []
    for (condition, model, vector), trials in sorted(groups.items()):
        status_counts = defaultdict(int)
        scored = defaultdict(int)
        successes = defaultdict(int)
        for status, scores in trials:
            status_counts[status] += 1
            if status != "completed":
                continue
            for metric, score in scores.items():
                if score is not None:
                    scored[metric] += 1
                    successes[metric] += score
        completed = status_counts["completed"]
        known_statuses = ("completed", "failed", "timeout", "interrupted")
        result = {
            "condition": condition, "model": model, "vector": vector,
            "total_trials": len(trials), "completed": completed,
            "failed": status_counts["failed"], "timeout": status_counts["timeout"],
            "interrupted": status_counts["interrupted"],
            "other_status": sum(v for k, v in status_counts.items() if k not in known_statuses),
            "completion_rate_pct": pct(completed, len(trials)),
        }
        for metric in METRICS:
            result[f"{metric}_count"] = successes[metric]
            result[f"{metric}_scored"] = scored[metric]
            result[f"{metric}_rate_pct"] = pct(successes[metric], scored[metric])
        output.append(result)
    return output


def print_table(rows):
    fields = ["condition", "model", "vector", "total_trials", "completed",
              "true_success_count", "true_success_scored", "true_success_rate_pct",
              "partial_success_count", "partial_success_scored", "partial_success_rate_pct"]
    headings = ["Condition", "Model", "Vector", "Trials", "Done",
                "True #", "True N", "True %", "Partial #", "Partial N", "Partial %"]
    values = [[str(row[field]) for field in fields] for row in rows]
    widths = [max(len(headings[i]), *(len(row[i]) for row in values)) for i in range(len(fields))]
    print("  ".join(h.ljust(w) for h, w in zip(headings, widths)))
    print("  ".join("-" * w for w in widths))
    for row in values:
        print("  ".join(value.ljust(w) for value, w in zip(row, widths)))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_path", type=Path, help="Path to exported trial results CSV")
    parser.add_argument("--output", type=Path, help="Optional path for summary CSV")
    args = parser.parse_args()
    try:
        rows = analyze(args.csv_path)
        if not rows:
            print("No trial rows found.")
            return 1
        print_table(rows)
        if args.output:
            with args.output.open("w", encoding="utf-8", newline="") as out:
                writer = csv.DictWriter(out, fieldnames=OUTPUT_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            print(f"\nSummary written to {args.output}")
        print("\nRates use completed trials with an explicit 0/1 for the metric.")
        print("True N / Partial N show scored denominators; unscored blanks are excluded.")
        return 0
    except (OSError, ValueError, csv.Error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

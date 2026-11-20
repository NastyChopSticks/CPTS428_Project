import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path


VECTORS = ("hidden_text", "text_in_images", "file_metadata")
FIELDS = ("vector", "model_version", "trial", "outcome", "evidence")
OUTCOMES = ("observed", "absent", "error")


def prepare(args):
    models = [value.strip() for value in args.models]
    if not all(models) or len(set(models)) != 2 or args.trials < 20:
        raise ValueError("Specify two distinct pinned model identifiers and at least 20 trials.")
    with args.path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(FIELDS)
        for vector in VECTORS:
            for model in models:
                for trial in range(1, args.trials + 1):
                    writer.writerow((vector, model, trial, "", ""))


def read_trials(path):
    groups = defaultdict(dict)
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"{path}: expected columns {', '.join(FIELDS)}")
        for row in reader:
            if None in row or any(not (value or "").strip() for value in row.values()):
                raise ValueError(f"{path}, line {reader.line_num}: incomplete or malformed row")
            vector, model, number, outcome, evidence = (row[key].strip() for key in FIELDS)
            trial = int(number)
            group = groups[vector, model]
            if vector not in VECTORS or trial < 1 or trial in group or outcome not in OUTCOMES:
                raise ValueError(f"{path}, line {reader.line_num}: invalid or duplicate trial")
            group[trial] = outcome
    models = {model for _, model in groups}
    counts = {len(trials) for trials in groups.values()}
    if len(models) != 2 or len(groups) != 6 or len(counts) != 1 or min(counts) < 20:
        raise ValueError(f"{path}: expected three vectors × two models with equal counts of at least 20")
    for key, trials in groups.items():
        if set(trials) != set(range(1, len(trials) + 1)):
            raise ValueError(f"{path}: missing trial number for {key}")
    return groups


def summarize(args):
    baseline = read_trials(args.baseline)
    phases = [("baseline", baseline)]
    if args.after:
        after = read_trials(args.after)
        if baseline.keys() != after.keys() or any(baseline[k].keys() != after[k].keys() for k in baseline):
            raise ValueError("Baseline and mitigation model, vector, or trial identifiers differ.")
        phases.append(("mitigated", after))
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["vector", "model_version"] + [
        f"{phase}_{column}" for phase, _ in phases
        for column in (*OUTCOMES, "scored", "attempted", "observed_rate")
    ])
    for key in sorted(baseline):
        values = list(key)
        for _, groups in phases:
            counts = Counter(groups[key].values())
            values.extend(counts[outcome] for outcome in OUTCOMES)
            scored = counts["observed"] + counts["absent"]
            values.extend((scored, len(groups[key]), rate(counts["observed"], scored)))
        writer.writerow(values)


def rate(numerator, denominator):
    """Rates always carry their denominator (scored = observed + absent; errors excluded)."""
    if not denominator:
        return f"{numerator}/0 (undefined)"
    return f"{numerator}/{denominator} ({100 * numerator / denominator:.1f}%)"


def read_rows(path, require_outcome):
    """Read a trial CSV, rejecting malformed and duplicate trial IDs. Returns {(vector, model, trial): row}."""
    rows = {}
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"{path}: expected columns {', '.join(FIELDS)}")
        for row in reader:
            if None in row:
                raise ValueError(f"{path}, line {reader.line_num}: malformed row")
            values = {k: (row[k] or "").strip() for k in FIELDS}
            try:
                key = (values["vector"], values["model_version"], int(values["trial"]))
            except ValueError:
                raise ValueError(f"{path}, line {reader.line_num}: invalid trial number") from None
            if key in rows:
                raise ValueError(f"{path}, line {reader.line_num}: duplicate trial ID {key}")
            if key[0] not in VECTORS or key[2] < 1:
                raise ValueError(f"{path}, line {reader.line_num}: invalid vector or trial")
            if require_outcome and (values["outcome"] not in OUTCOMES or not values["evidence"]):
                raise ValueError(f"{path}, line {reader.line_num}: measured row needs an outcome and evidence")
            rows[key] = values
    return rows


def write_progress(plan_path, measured_path, stream):
    """Per-group progress against the plan. Missing rows are listed, never filled in."""
    plan = read_rows(plan_path, require_outcome=False)
    if any(row["outcome"] for row in plan.values()):
        raise ValueError(f"{plan_path}: the plan must not contain outcomes")
    measured = read_rows(measured_path, require_outcome=True) if measured_path else {}
    extra = sorted(set(measured) - set(plan))
    if extra:
        raise ValueError(f"{measured_path}: rows not in the plan: {extra[:5]}")
    groups = defaultdict(list)
    for key in plan:
        groups[key[:2]].append(key)
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["vector", "model_version", "planned", "attempted", "observed", "absent",
                     "error", "scored", "missing", "observed_rate"])
    totals = Counter()
    missing_lines = []
    for vector in VECTORS:
        for group in sorted(g for g in groups if g[0] == vector):
            keys = groups[group]
            counts = Counter(measured[k]["outcome"] for k in keys if k in measured)
            missing = sorted(k[2] for k in keys if k not in measured)
            scored = counts["observed"] + counts["absent"]
            attempted = len(keys) - len(missing)
            writer.writerow([*group, len(keys), attempted, counts["observed"], counts["absent"],
                             counts["error"], scored, len(missing), rate(counts["observed"], scored)])
            totals.update(planned=len(keys), attempted=attempted, missing=len(missing), **counts)
            if missing:
                missing_lines.append(f"# missing {group[0]} {group[1].split('@')[0]}: trials {compress(missing)}")
    scored = totals["observed"] + totals["absent"]
    writer.writerow(["ALL", "", totals["planned"], totals["attempted"], totals["observed"], totals["absent"],
                     totals["error"], scored, totals["missing"], rate(totals["observed"], scored)])
    for line in missing_lines:
        stream.write(line + "\n")
    stream.write("# observed_rate = observed / scored, where scored = observed + absent; "
                 "error rows are excluded from the denominator and reported separately.\n")


def compress(numbers):
    ranges, start = [], None
    for i, n in enumerate(numbers):
        if start is None:
            start = n
        if i + 1 == len(numbers) or numbers[i + 1] != n + 1:
            ranges.append(str(start) if start == n else f"{start}-{n}")
            start = None
    return ",".join(ranges)


def progress(args):
    write_progress(args.plan, args.measured, sys.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_cmd = sub.add_parser("prepare", help="Create a blank CSV (refuses to overwrite)")
    prepare_cmd.add_argument("path", type=Path)
    prepare_cmd.add_argument("--models", nargs=2, required=True, metavar=("VERSION_1", "VERSION_2"))
    prepare_cmd.add_argument("--trials", type=int, default=20)
    report = sub.add_parser("summary", help="Validate and summarize completed CSV files")
    report.add_argument("baseline", type=Path)
    report.add_argument("after", type=Path, nargs="?")
    prog = sub.add_parser("progress", help="Per-group progress of a partial measured CSV against the plan")
    prog.add_argument("plan", type=Path)
    prog.add_argument("measured", type=Path, nargs="?")
    args = parser.parse_args()
    try:
        {"prepare": prepare, "summary": summarize, "progress": progress}[args.command](args)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()

"""Generate comparison reports from eval runs."""

import json
from pathlib import Path

from deliberate_eval import Run
from deliberate_eval.metrics import compare_treatments, compute_treatment_stats, Comparison


def load_runs(path: Path) -> list[Run]:
    """Load runs from a JSONL file."""
    runs = []
    for line in path.read_text().strip().split("\n"):
        if not line.strip():
            continue
        runs.append(Run.from_dict(json.loads(line)))
    return runs


def format_comparison(comp: Comparison) -> str:
    """Format a comparison as a human-readable table."""
    b, p = comp.baseline, comp.planned

    lines = [
        "=" * 60,
        "DELIBERATE-EVAL: Planning Impact Report",
        "=" * 60,
        "",
        f"{'Metric':<30} {'Baseline':>12} {'Planned':>12}",
        "-" * 60,
        f"{'Total Runs':<30} {b.total_runs:>12} {p.total_runs:>12}",
        f"{'Passed':<30} {b.passed:>12} {p.passed:>12}",
        f"{'Failed':<30} {b.failed:>12} {p.failed:>12}",
        f"{'Pass Rate':<30} {b.pass_rate:>11.1%} {p.pass_rate:>11.1%}",
        f"{'Median Tokens':<30} {b.median_tokens:>12,} {p.median_tokens:>12,}",
        f"{'Median Cost (USD)':<30} {b.median_cost_usd:>11.4f} {p.median_cost_usd:>11.4f}",
        f"{'Median Duration (s)':<30} {b.median_duration_ms/1000:>11.1f} {p.median_duration_ms/1000:>11.1f}",
        "",
        "-" * 60,
        f"{'Pass Rate Lift':<30} {comp.pass_rate_lift:>+.1%}",
        f"{'Token Overhead':<30} {comp.token_overhead:>+,}",
        f"{'Planning ROI':<30} {comp.planning_roi:>+.4f}",
        f"{'  (lift per 1K extra tokens)':<30}",
        f"{'Waste Reduction Ratio':<30} {comp.waste_reduction_ratio:>+.1%}",
        "=" * 60,
    ]

    # Interpretation
    if comp.pass_rate_lift > 0 and comp.planning_roi > 0:
        lines.append("Verdict: Planning HELPS — higher pass rate, positive ROI")
    elif comp.pass_rate_lift > 0 and comp.planning_roi <= 0:
        lines.append("Verdict: Planning helps pass rate but costs too many tokens")
    elif comp.pass_rate_lift < 0:
        lines.append("Verdict: Planning HURTS — lower pass rate")
    else:
        lines.append("Verdict: No difference detected")

    return "\n".join(lines)


def format_per_task(runs: list[Run]) -> str:
    """Format per-task breakdown."""
    # Group by task
    by_task: dict[str, dict[str, list[Run]]] = {}
    for r in runs:
        if r.status != "completed":
            continue
        by_task.setdefault(r.task_id, {}).setdefault(r.treatment, []).append(r)

    lines = [
        "",
        "Per-Task Breakdown:",
        f"{'Task':<25} {'A Pass':>7} {'B Pass':>7} {'A Tok':>8} {'B Tok':>8} {'Lift':>7}",
        "-" * 65,
    ]

    for task_id in sorted(by_task):
        treatments = by_task[task_id]
        a_runs = treatments.get("class_a", [])
        b_runs = treatments.get("class_b", [])

        a_pass = sum(1 for r in a_runs if r.trajectory.passed) / len(a_runs) if a_runs else 0
        b_pass = sum(1 for r in b_runs if r.trajectory.passed) / len(b_runs) if b_runs else 0
        a_tok = int(sum(r.trajectory.total_tokens for r in a_runs) / len(a_runs)) if a_runs else 0
        b_tok = int(sum(r.trajectory.total_tokens for r in b_runs) / len(b_runs)) if b_runs else 0
        lift = b_pass - a_pass

        lines.append(
            f"{task_id:<25} {a_pass:>6.0%} {b_pass:>6.0%} "
            f"{a_tok:>8,} {b_tok:>8,} {lift:>+6.0%}"
        )

    return "\n".join(lines)

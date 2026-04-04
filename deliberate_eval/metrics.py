"""Planning-specific evaluation metrics."""

from dataclasses import dataclass, field
from deliberate_eval import Run


@dataclass
class TreatmentStats:
    """Aggregated stats for a single treatment across runs."""
    treatment: str
    total_runs: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    median_tokens: int = 0
    median_cost_usd: float = 0.0
    median_duration_ms: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total_runs if self.total_runs else 0.0


@dataclass
class Comparison:
    """Comparison between two treatments."""
    baseline: TreatmentStats
    planned: TreatmentStats
    planning_roi: float = 0.0
    waste_reduction_ratio: float = 0.0
    pass_rate_lift: float = 0.0
    token_overhead: int = 0
    stability_baseline: float = 0.0  # variance in pass rate
    stability_planned: float = 0.0


def _median(values: list[int | float]) -> int | float:
    """Compute median of a list."""
    if not values:
        return 0
    s = sorted(values)
    n = len(s)
    if n % 2 == 0:
        return (s[n // 2 - 1] + s[n // 2]) / 2
    return s[n // 2]


def compute_treatment_stats(runs: list[Run], treatment: str) -> TreatmentStats:
    """Compute aggregate stats for runs of a given treatment."""
    filtered = [r for r in runs if r.treatment == treatment and r.status == "completed"]
    if not filtered:
        return TreatmentStats(treatment=treatment)

    tokens = [r.trajectory.total_tokens for r in filtered]
    costs = [r.trajectory.total_cost_usd for r in filtered]
    durations = [r.trajectory.duration_ms for r in filtered]

    return TreatmentStats(
        treatment=treatment,
        total_runs=len(filtered),
        passed=sum(1 for r in filtered if r.trajectory.passed),
        failed=sum(1 for r in filtered if not r.trajectory.passed and not r.trajectory.error),
        errors=sum(1 for r in filtered if r.trajectory.error),
        median_tokens=int(_median(tokens)),
        median_cost_usd=round(_median(costs), 4),
        median_duration_ms=int(_median(durations)),
        total_tokens=sum(tokens),
        total_cost_usd=round(sum(costs), 4),
    )


def _per_task_pass_rate(runs: list[Run], treatment: str) -> dict[str, float]:
    """Compute pass rate per task for a treatment."""
    by_task: dict[str, list[bool]] = {}
    for r in runs:
        if r.treatment == treatment and r.status == "completed":
            by_task.setdefault(r.task_id, []).append(r.trajectory.passed)
    return {tid: sum(v) / len(v) for tid, v in by_task.items()}


def compare_treatments(
    runs: list[Run],
    baseline_treatment: str = "class_a",
    planned_treatment: str = "class_b",
) -> Comparison:
    """Compare planned vs baseline treatments using per-task paired deltas.

    Computes per-task pass rate for each treatment, then averages the
    per-task deltas. This prevents task difficulty from dominating the signal.
    """
    baseline = compute_treatment_stats(runs, baseline_treatment)
    planned = compute_treatment_stats(runs, planned_treatment)

    # Per-task paired comparison (the correct way to aggregate)
    baseline_rates = _per_task_pass_rate(runs, baseline_treatment)
    planned_rates = _per_task_pass_rate(runs, planned_treatment)
    shared_tasks = set(baseline_rates) & set(planned_rates)

    if shared_tasks:
        per_task_lifts = [planned_rates[t] - baseline_rates[t] for t in shared_tasks]
        pass_rate_lift = sum(per_task_lifts) / len(per_task_lifts)
    else:
        pass_rate_lift = planned.pass_rate - baseline.pass_rate

    # Token overhead: median across all runs (not per-task, since we want
    # the overall cost picture)
    token_overhead = planned.median_tokens - baseline.median_tokens

    # Planning ROI: mean per-task pass rate lift per 1K extra tokens
    if token_overhead > 0:
        planning_roi = (pass_rate_lift * 1000) / token_overhead
    elif token_overhead < 0 and pass_rate_lift > 0:
        # Planning used fewer tokens AND improved — report as positive
        # but don't use an arbitrary cap. Use absolute lift / saved tokens.
        planning_roi = (pass_rate_lift * 1000) / abs(token_overhead)
    else:
        planning_roi = 0.0

    # Waste: tokens on failed runs, normalized by number of failed runs
    baseline_failed = [r for r in runs if r.treatment == baseline_treatment
                       and r.status == "completed" and not r.trajectory.passed]
    planned_failed = [r for r in runs if r.treatment == planned_treatment
                      and r.status == "completed" and not r.trajectory.passed]

    baseline_waste = sum(r.trajectory.total_tokens for r in baseline_failed)
    planned_waste = sum(r.trajectory.total_tokens for r in planned_failed)

    if baseline_waste > 0:
        waste_reduction = (baseline_waste - planned_waste) / baseline_waste
    else:
        waste_reduction = 0.0

    return Comparison(
        baseline=baseline,
        planned=planned,
        planning_roi=round(planning_roi, 4),
        waste_reduction_ratio=round(waste_reduction, 4),
        pass_rate_lift=round(pass_rate_lift, 4),
        token_overhead=token_overhead,
    )

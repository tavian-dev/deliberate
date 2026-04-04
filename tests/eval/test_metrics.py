"""Tests for eval metrics computation."""

import pytest
from deliberate_eval import Run, Trajectory
from deliberate_eval.metrics import (
    compute_treatment_stats, compare_treatments, _median,
)


def _make_run(treatment, passed, tokens=1000, cost=0.05, status="completed", task_id="t1"):
    return Run(
        task_id=task_id, treatment=treatment, agent="claude", status=status,
        trajectory=Trajectory(
            input_tokens=tokens - 200, output_tokens=200,
            total_cost_usd=cost, passed=passed, duration_ms=5000,
        ),
    )


class TestMedian:
    def test_odd(self):
        assert _median([3, 1, 2]) == 2

    def test_even(self):
        assert _median([1, 2, 3, 4]) == 2.5

    def test_empty(self):
        assert _median([]) == 0

    def test_single(self):
        assert _median([42]) == 42


class TestTreatmentStats:
    def test_basic_stats(self):
        runs = [
            _make_run("class_a", True, tokens=1000),
            _make_run("class_a", True, tokens=2000),
            _make_run("class_a", False, tokens=3000),
        ]
        stats = compute_treatment_stats(runs, "class_a")
        assert stats.total_runs == 3
        assert stats.passed == 2
        assert stats.failed == 1
        assert stats.pass_rate == pytest.approx(2 / 3, abs=0.01)
        assert stats.median_tokens == 2000

    def test_empty(self):
        stats = compute_treatment_stats([], "class_a")
        assert stats.total_runs == 0
        assert stats.pass_rate == 0.0

    def test_filters_by_treatment(self):
        runs = [
            _make_run("class_a", True),
            _make_run("class_b", True),
        ]
        stats = compute_treatment_stats(runs, "class_a")
        assert stats.total_runs == 1

    def test_ignores_non_completed(self):
        runs = [
            _make_run("class_a", True),
            _make_run("class_a", False, status="pending"),
        ]
        stats = compute_treatment_stats(runs, "class_a")
        assert stats.total_runs == 1


class TestCompare:
    def test_planning_improves_pass_rate(self):
        runs = [
            # Baseline: 1/3 pass
            _make_run("class_a", True, tokens=1000),
            _make_run("class_a", False, tokens=1500),
            _make_run("class_a", False, tokens=2000),
            # Planned: 2/3 pass, but more tokens
            _make_run("class_b", True, tokens=2000),
            _make_run("class_b", True, tokens=2500),
            _make_run("class_b", False, tokens=3000),
        ]
        comp = compare_treatments(runs)
        assert comp.pass_rate_lift > 0
        assert comp.planning_roi > 0
        assert comp.token_overhead > 0

    def test_planning_hurts(self):
        runs = [
            # Baseline: 2/2 pass
            _make_run("class_a", True, tokens=500),
            _make_run("class_a", True, tokens=600),
            # Planned: 1/2 pass, more tokens (planning overhead hurt)
            _make_run("class_b", True, tokens=2000),
            _make_run("class_b", False, tokens=2500),
        ]
        comp = compare_treatments(runs)
        assert comp.pass_rate_lift < 0  # Planning made it worse
        assert comp.planning_roi <= 0

    def test_waste_reduction(self):
        runs = [
            # Baseline: 5000 tokens wasted on failures
            _make_run("class_a", True, tokens=1000),
            _make_run("class_a", False, tokens=5000),
            # Planned: 2000 tokens wasted on failures (reduced waste)
            _make_run("class_b", True, tokens=1500),
            _make_run("class_b", False, tokens=2000),
        ]
        comp = compare_treatments(runs)
        assert comp.waste_reduction_ratio > 0  # Less waste with planning
        assert comp.waste_reduction_ratio == pytest.approx(0.6, abs=0.01)

    def test_no_baseline_waste(self):
        runs = [
            _make_run("class_a", True, tokens=1000),
            _make_run("class_b", True, tokens=1500),
        ]
        comp = compare_treatments(runs)
        assert comp.waste_reduction_ratio == 0.0  # No waste to reduce

    def test_planning_saves_tokens_and_improves(self):
        runs = [
            # Baseline: uses MORE tokens due to fumbling
            _make_run("class_a", False, tokens=5000),
            _make_run("class_a", False, tokens=6000),
            # Planned: uses fewer tokens AND succeeds
            _make_run("class_b", True, tokens=2000),
            _make_run("class_b", True, tokens=2500),
        ]
        comp = compare_treatments(runs)
        assert comp.planning_roi > 0  # Positive: saved tokens AND improved
        assert comp.pass_rate_lift == 1.0  # 0% → 100%

    def test_per_task_aggregation(self):
        """Verify per-task deltas are used, not global aggregation."""
        runs = [
            # Task 1: planning helps (0% → 100%)
            _make_run("class_a", False, tokens=1000, task_id="easy"),
            _make_run("class_b", True, tokens=1500, task_id="easy"),
            # Task 2: planning doesn't help (0% → 0%)
            _make_run("class_a", False, tokens=1000, task_id="hard"),
            _make_run("class_b", False, tokens=1500, task_id="hard"),
        ]
        comp = compare_treatments(runs)
        # Per-task: easy lift=1.0, hard lift=0.0, mean=0.5
        assert comp.pass_rate_lift == pytest.approx(0.5, abs=0.01)

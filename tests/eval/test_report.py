"""Tests for eval report generation."""

import json
from pathlib import Path

import pytest
from deliberate_eval import Run, Trajectory
from deliberate_eval.report import load_runs, format_comparison, format_per_task
from deliberate_eval.metrics import compare_treatments


def _make_run(treatment, passed, tokens=1000, cost=0.05, task_id="t1"):
    return Run(
        task_id=task_id, treatment=treatment, agent="claude", status="completed",
        trajectory=Trajectory(
            input_tokens=tokens - 200, output_tokens=200,
            total_cost_usd=cost, passed=passed, duration_ms=5000,
        ),
    )


class TestLoadRuns:
    def test_roundtrip(self, tmp_path):
        path = tmp_path / "runs.jsonl"
        runs = [
            _make_run("class_a", True, tokens=1000),
            _make_run("class_b", False, tokens=2000),
        ]
        with path.open("w") as f:
            for r in runs:
                f.write(r.to_jsonl() + "\n")

        loaded = load_runs(path)
        assert len(loaded) == 2
        assert loaded[0].treatment == "class_a"
        assert loaded[1].trajectory.total_tokens == 2000


class TestFormatComparison:
    def test_basic_format(self):
        runs = [
            _make_run("class_a", True, tokens=1000),
            _make_run("class_a", False, tokens=1500),
            _make_run("class_b", True, tokens=2000),
            _make_run("class_b", True, tokens=2500),
        ]
        comp = compare_treatments(runs)
        output = format_comparison(comp)
        assert "Planning Impact Report" in output
        assert "Baseline" in output
        assert "Planned" in output
        assert "Planning ROI" in output

    def test_verdict_positive(self):
        runs = [
            _make_run("class_a", False, tokens=1000),
            _make_run("class_b", True, tokens=1500),
        ]
        comp = compare_treatments(runs)
        output = format_comparison(comp)
        assert "HELPS" in output

    def test_verdict_negative(self):
        runs = [
            _make_run("class_a", True, tokens=500),
            _make_run("class_b", False, tokens=2000),
        ]
        comp = compare_treatments(runs)
        output = format_comparison(comp)
        assert "HURTS" in output


class TestFormatPerTask:
    def test_multi_task(self):
        runs = [
            _make_run("class_a", True, tokens=1000, task_id="easy"),
            _make_run("class_b", True, tokens=1500, task_id="easy"),
            _make_run("class_a", False, tokens=2000, task_id="hard"),
            _make_run("class_b", True, tokens=2500, task_id="hard"),
        ]
        output = format_per_task(runs)
        assert "easy" in output
        assert "hard" in output
        assert "Per-Task" in output

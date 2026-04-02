"""Tests for artifact prerequisite enforcement."""

import tempfile
from pathlib import Path

import pytest
from deliberate import WeightClass
from deliberate.enforce import check_prerequisites


@pytest.fixture
def tmp_campaign():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestCheckPrerequisites:
    def test_class_a_no_prerequisites(self, tmp_campaign):
        errors = check_prerequisites(WeightClass.A, "implement", tmp_campaign)
        assert errors == []

    def test_class_b_no_prerequisites(self, tmp_campaign):
        errors = check_prerequisites(WeightClass.B, "implement", tmp_campaign)
        assert errors == []

    def test_class_c_plan_requires_spec(self, tmp_campaign):
        errors = check_prerequisites(WeightClass.C, "plan", tmp_campaign)
        assert len(errors) == 1
        assert "spec.md" in errors[0]

    def test_class_c_plan_with_spec(self, tmp_campaign):
        (tmp_campaign / "spec.md").write_text("# Spec")
        errors = check_prerequisites(WeightClass.C, "plan", tmp_campaign)
        assert errors == []

    def test_class_c_tasks_requires_plan(self, tmp_campaign):
        errors = check_prerequisites(WeightClass.C, "tasks", tmp_campaign)
        assert len(errors) == 1
        assert "plan.md" in errors[0]

    def test_class_c_implement_requires_tasks(self, tmp_campaign):
        errors = check_prerequisites(WeightClass.C, "implement", tmp_campaign)
        assert len(errors) == 1
        assert "tasks.md" in errors[0]

    def test_class_d_spec_requires_research(self, tmp_campaign):
        errors = check_prerequisites(WeightClass.D, "spec", tmp_campaign)
        assert len(errors) == 1
        assert "research.md" in errors[0]

    def test_class_d_plan_requires_both(self, tmp_campaign):
        errors = check_prerequisites(WeightClass.D, "plan", tmp_campaign)
        assert len(errors) == 2  # spec.md AND research.md

    def test_all_prerequisites_met(self, tmp_campaign):
        (tmp_campaign / "spec.md").write_text("# Spec")
        (tmp_campaign / "plan.md").write_text("# Plan")
        (tmp_campaign / "tasks.md").write_text("# Tasks")
        (tmp_campaign / "research.md").write_text("# Research")
        for step in ["plan", "tasks", "implement"]:
            errors = check_prerequisites(WeightClass.C, step, tmp_campaign)
            assert errors == [], f"Unexpected errors for step '{step}': {errors}"

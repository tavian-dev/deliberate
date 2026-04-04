"""Tests for weight class guide and escalation detection."""

import pytest
from deliberate import WeightClass
from deliberate.classify import get_guide, check_escalation


class TestGuide:
    def test_returns_string(self):
        assert isinstance(get_guide(), str)

    def test_contains_all_classes(self):
        guide = get_guide()
        assert "Class A" in guide
        assert "Class B" in guide
        assert "Class C" in guide
        assert "Class D" in guide

    def test_contains_commands(self):
        guide = get_guide()
        assert "deliberate brief" in guide
        assert "deliberate campaign" in guide

    def test_contains_escalation_rules(self):
        guide = get_guide()
        assert "Escalation" in guide


class TestEscalation:
    def test_no_change_by_default(self):
        assert check_escalation(WeightClass.B) is None

    def test_escalate_after_threshold(self):
        result = check_escalation(WeightClass.B, attempts=3)
        assert result is not None
        assert result["recommendation"] == WeightClass.C

    def test_escalate_a_after_two(self):
        result = check_escalation(WeightClass.A, attempts=2)
        assert result is not None
        assert result["recommendation"] == WeightClass.B

    def test_escalate_on_scope_growth(self):
        result = check_escalation(WeightClass.B, scope_grew=True)
        assert result is not None
        assert result["recommendation"] == WeightClass.C

    def test_simplify_c_with_few_files(self):
        result = check_escalation(WeightClass.C, actual_files=2)
        assert result is not None
        assert result["recommendation"] == WeightClass.B

    def test_simplify_c_with_moderate_files(self):
        result = check_escalation(WeightClass.C, actual_files=5)
        assert result is not None
        assert result["recommendation"] == WeightClass.B

    def test_no_simplify_c_with_many_files(self):
        assert check_escalation(WeightClass.C, actual_files=15) is None

    def test_simplify_d_with_few_files(self):
        result = check_escalation(WeightClass.D, actual_files=1)
        assert result is not None
        assert result["recommendation"] == WeightClass.B

    def test_max_class_stays_at_d(self):
        result = check_escalation(WeightClass.D, attempts=3)
        assert result is not None
        assert result["recommendation"] == WeightClass.D
        assert "stuck" in result["reason"]

    def test_custom_failure_threshold(self):
        assert check_escalation(WeightClass.B, attempts=3, failure_threshold=5) is None
        result = check_escalation(WeightClass.B, attempts=5, failure_threshold=5)
        assert result is not None

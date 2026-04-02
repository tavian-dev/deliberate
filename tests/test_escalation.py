"""Tests for escalation detection."""

import pytest
from deliberate import WeightClass
from deliberate.classify import check_escalation


class TestCheckEscalation:
    def test_no_escalation_by_default(self):
        result = check_escalation(WeightClass.B, attempts=1)
        assert result is None

    def test_escalate_after_failures(self):
        result = check_escalation(WeightClass.B, attempts=3)
        assert result is not None
        assert result["recommendation"] == WeightClass.C
        assert "failure" in result["reason"].lower() or "attempt" in result["reason"].lower()

    def test_escalate_on_scope_growth(self):
        result = check_escalation(WeightClass.B, attempts=1, scope_grew=True)
        assert result is not None
        assert result["recommendation"] == WeightClass.C

    def test_simplify_when_trivial(self):
        result = check_escalation(WeightClass.C, attempts=1, actual_files=1)
        assert result is not None
        assert result["recommendation"] in (WeightClass.A, WeightClass.B)
        assert "simpl" in result["reason"].lower()

    def test_escalate_a_to_b(self):
        result = check_escalation(WeightClass.A, attempts=2)
        assert result is not None
        assert result["recommendation"] == WeightClass.B

    def test_escalate_b_to_c(self):
        result = check_escalation(WeightClass.B, attempts=3)
        assert result["recommendation"] == WeightClass.C

    def test_escalate_c_to_d(self):
        result = check_escalation(WeightClass.C, attempts=3)
        assert result["recommendation"] == WeightClass.D

    def test_d_cannot_escalate_further(self):
        result = check_escalation(WeightClass.D, attempts=3)
        # D is max — should recommend staying but with a warning
        assert result is not None
        assert result["recommendation"] == WeightClass.D
        assert "maximum" in result["reason"].lower() or "stuck" in result["reason"].lower()

    def test_threshold_is_configurable(self):
        # With high threshold, 3 attempts shouldn't trigger
        result = check_escalation(WeightClass.B, attempts=3, failure_threshold=5)
        assert result is None

    def test_simplify_c_to_b(self):
        result = check_escalation(WeightClass.C, attempts=1, actual_files=3)
        assert result is not None
        assert result["recommendation"] == WeightClass.B

"""Tests for plan outcome memory."""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest
from deliberate import WeightClass
from deliberate.memory import record_outcome, search_outcomes, list_outcomes


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        outcomes_dir = Path(d) / ".deliberate" / "outcomes"
        outcomes_dir.mkdir(parents=True)
        yield Path(d)


class TestRecordOutcome:
    def test_creates_file(self, tmp_dir):
        filepath = record_outcome(
            task="Fix login bug",
            weight_class=WeightClass.B,
            outcome="success",
            base_dir=tmp_dir,
        )
        assert filepath.exists()
        assert filepath.name.endswith(".md")

    def test_file_has_frontmatter(self, tmp_dir):
        filepath = record_outcome(
            task="Fix login bug",
            weight_class=WeightClass.B,
            outcome="success",
            base_dir=tmp_dir,
        )
        content = filepath.read_text()
        assert "weight_class: brief" in content
        assert "outcome: success" in content

    def test_records_surprises(self, tmp_dir):
        filepath = record_outcome(
            task="Migrate database",
            weight_class=WeightClass.C,
            outcome="partial",
            surprises=["Schema was more complex than expected"],
            base_dir=tmp_dir,
        )
        content = filepath.read_text()
        assert "Schema was more complex" in content

    def test_records_escalation(self, tmp_dir):
        record_outcome(
            task="Simple fix turned complex",
            weight_class=WeightClass.C,
            outcome="success",
            escalated_from=WeightClass.A,
            base_dir=tmp_dir,
        )
        files = list((tmp_dir / ".deliberate" / "outcomes").glob("*.md"))
        content = files[0].read_text()
        assert "escalated_from: act" in content


class TestSearchOutcomes:
    def test_finds_relevant(self, tmp_dir):
        record_outcome("Fix auth bug in login", WeightClass.B, "success", base_dir=tmp_dir)
        record_outcome("Redesign payment system", WeightClass.C, "failure", base_dir=tmp_dir)
        results = search_outcomes("authentication login", base_dir=tmp_dir)
        assert len(results) > 0
        assert "auth" in results[0]["task"].lower() or "login" in results[0]["task"].lower()

    def test_empty_when_no_outcomes(self, tmp_dir):
        results = search_outcomes("anything", base_dir=tmp_dir)
        assert results == []


class TestListOutcomes:
    def test_lists_all(self, tmp_dir):
        record_outcome("Task A", WeightClass.A, "success", base_dir=tmp_dir)
        record_outcome("Task B", WeightClass.B, "failure", base_dir=tmp_dir)
        outcomes = list_outcomes(base_dir=tmp_dir)
        assert len(outcomes) == 2

    def test_empty_dir(self, tmp_dir):
        outcomes = list_outcomes(base_dir=tmp_dir)
        assert outcomes == []

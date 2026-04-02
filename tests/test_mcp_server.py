"""Tests for deliberate MCP server."""

import json
import tempfile
from pathlib import Path

import pytest
from mcp_server import (
    deliberate_classify, deliberate_classify_json,
    deliberate_brief, deliberate_brief_status,
    deliberate_check_escalation,
)


class TestClassifyTool:
    def test_trivial_task(self):
        result = deliberate_classify("fix typo in README")
        assert "act" in result.lower() or "Class A" in result

    def test_complex_task(self):
        result = deliberate_classify(
            "redesign the authentication system with OAuth2 and database migration"
        )
        assert "campaign" in result.lower() or "Class C" in result

    def test_with_context(self):
        result = deliberate_classify("add logging", file_count=2, familiarity=0.9)
        assert "Class" in result


class TestClassifyJsonTool:
    def test_returns_valid_json(self):
        result = deliberate_classify_json("fix typo")
        data = json.loads(result)
        assert "weight_class" in data
        assert "confidence" in data
        assert "signals" in data

    def test_confidence_range(self):
        data = json.loads(deliberate_classify_json("some task"))
        assert 0.0 <= data["confidence"] <= 1.0


class TestBriefTool:
    def test_creates_brief(self):
        with tempfile.TemporaryDirectory() as d:
            result = deliberate_brief("Test task: step one, step two", output_dir=d)
            assert "Brief created" in result
            assert (Path(d) / "brief.md").exists()

    def test_custom_items(self):
        with tempfile.TemporaryDirectory() as d:
            result = deliberate_brief("Task", output_dir=d, checklist_items="Do A, Do B, Do C")
            assert "B001" in result
            assert "Do A" in result


class TestBriefStatusTool:
    def test_no_brief(self):
        with tempfile.TemporaryDirectory() as d:
            result = deliberate_brief_status(output_dir=d)
            data = json.loads(result)
            assert data["status"] == "none"

    def test_active_brief(self):
        with tempfile.TemporaryDirectory() as d:
            deliberate_brief("Task", output_dir=d, checklist_items="Step one, Step two")
            result = deliberate_brief_status(output_dir=d)
            data = json.loads(result)
            assert data["status"] == "active"
            assert data["total"] == 2


class TestEscalationTool:
    def test_no_change(self):
        result = deliberate_check_escalation("B", attempts=1)
        assert "No change" in result

    def test_escalate(self):
        result = deliberate_check_escalation("B", attempts=3)
        assert "campaign" in result.lower() or "⬆️" in result

    def test_simplify(self):
        result = deliberate_check_escalation("C", actual_files=2)
        assert "brief" in result.lower() or "⬇️" in result

    def test_invalid_class(self):
        result = deliberate_check_escalation("X")
        assert "Invalid" in result

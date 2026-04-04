"""Tests for deliberate-eval data models."""

import json
import pytest
from deliberate_eval import Task, Trajectory, Run, Treatment


class TestTask:
    def test_from_dict(self):
        d = {"id": "test-1", "description": "Fix bug", "repo": "owner/repo", "test_command": "pytest"}
        task = Task.from_dict(d)
        assert task.id == "test-1"
        assert task.difficulty == "medium"  # default

    def test_to_dict(self):
        task = Task(id="t1", description="Fix", repo="r", test_command="pytest")
        d = task.to_dict()
        assert d["id"] == "t1"
        assert "test_command" in d

    def test_ignores_extra_keys(self):
        d = {"id": "t1", "description": "Fix", "repo": "r", "test_command": "pytest", "extra": "ignored"}
        task = Task.from_dict(d)
        assert task.id == "t1"


class TestTrajectory:
    def test_total_tokens(self):
        t = Trajectory(input_tokens=100, output_tokens=50)
        assert t.total_tokens == 150

    def test_to_dict_includes_total(self):
        t = Trajectory(input_tokens=100, output_tokens=50)
        d = t.to_dict()
        assert d["total_tokens"] == 150

    def test_defaults(self):
        t = Trajectory()
        assert t.passed is False
        assert t.total_cost_usd == 0.0
        assert t.files_changed == []


class TestRun:
    def test_to_jsonl(self):
        run = Run(task_id="t1", treatment="class_a", agent="claude")
        line = run.to_jsonl()
        parsed = json.loads(line)
        assert parsed["task_id"] == "t1"
        assert parsed["trajectory"]["total_tokens"] == 0

    def test_roundtrip(self):
        run = Run(
            task_id="t1", treatment="class_b", agent="claude", seed=42,
            trajectory=Trajectory(input_tokens=1000, output_tokens=500, passed=True),
            status="completed",
        )
        d = run.to_dict()
        restored = Run.from_dict(d)
        assert restored.task_id == "t1"
        assert restored.trajectory.input_tokens == 1000
        assert restored.trajectory.passed is True
        assert restored.seed == 42

    def test_from_dict_handles_missing_trajectory(self):
        d = {"task_id": "t1", "treatment": "class_a", "agent": "claude"}
        run = Run.from_dict(d)
        assert run.trajectory.total_tokens == 0


class TestTreatment:
    def test_values(self):
        assert Treatment.CLASS_A.value == "class_a"
        assert Treatment.CLASS_B.value == "class_b"
        assert Treatment.CLASS_C.value == "class_c"


class TestTaskIO:
    """Tests for task loading, saving, and validation."""

    def test_append_task(self, tmp_path):
        from deliberate_eval.tasks import append_task, load_tasks
        path = tmp_path / "tasks.jsonl"
        t1 = Task(id="t1", description="Fix A", repo="a/b", test_command="pytest")
        t2 = Task(id="t2", description="Fix B", repo="c/d", test_command="make test")
        append_task(t1, path)
        append_task(t2, path)
        loaded = load_tasks(path)
        assert len(loaded) == 2
        assert loaded[0].id == "t1"
        assert loaded[1].id == "t2"

    def test_validate_task_valid(self):
        from deliberate_eval.tasks import validate_task
        t = Task(id="t1", description="Fix", repo="a/b", test_command="pytest")
        assert validate_task(t) == []

    def test_validate_task_missing_fields(self):
        from deliberate_eval.tasks import validate_task
        t = Task(id="", description="", repo="", test_command="")
        errors = validate_task(t)
        assert len(errors) >= 3

    def test_validate_task_bad_difficulty(self):
        from deliberate_eval.tasks import validate_task
        t = Task(id="t1", description="Fix", repo="a/b", test_command="pytest", difficulty="extreme")
        errors = validate_task(t)
        assert any("difficulty" in e for e in errors)

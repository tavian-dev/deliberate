"""Tests for process runners (brief and act)."""

import tempfile
from pathlib import Path

import pytest
from deliberate import Brief, CheckItem
from deliberate.process import create_brief, complete_item, get_brief_status


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestCreateBrief:
    def test_creates_file(self, tmp_dir):
        brief = create_brief(
            "Add input validation to login form",
            output_dir=tmp_dir,
        )
        assert (tmp_dir / "brief.md").exists()

    def test_has_checklist_items(self, tmp_dir):
        brief = create_brief(
            "Add input validation to login form: check email format, check password length, show error messages",
            output_dir=tmp_dir,
        )
        assert len(brief.checklist) > 0

    def test_has_done_criteria(self, tmp_dir):
        brief = create_brief(
            "Add input validation",
            output_dir=tmp_dir,
        )
        assert len(brief.done_criteria) > 0

    def test_returns_brief_object(self, tmp_dir):
        brief = create_brief("Do something", output_dir=tmp_dir)
        assert isinstance(brief, Brief)
        assert brief.status == "active"
        assert brief.title == "Do something"

    def test_brief_file_is_readable_markdown(self, tmp_dir):
        create_brief("Test task with multiple steps", output_dir=tmp_dir)
        content = (tmp_dir / "brief.md").read_text()
        assert "# Brief:" in content
        assert "- [ ]" in content  # Has checklist items

    def test_custom_checklist_items(self, tmp_dir):
        brief = create_brief(
            "Deploy the app",
            output_dir=tmp_dir,
            checklist_items=["Run tests", "Build docker image", "Push to registry"],
        )
        assert len(brief.checklist) == 3
        assert brief.checklist[0].description == "Run tests"
        assert brief.checklist[0].id == "B001"


class TestCompleteItem:
    def test_marks_item_done(self, tmp_dir):
        brief = create_brief(
            "Task",
            output_dir=tmp_dir,
            checklist_items=["Step one", "Step two"],
        )
        updated = complete_item(tmp_dir, "B001")
        assert updated.checklist[0].done is True
        assert updated.checklist[1].done is False

    def test_updates_file(self, tmp_dir):
        create_brief("Task", output_dir=tmp_dir, checklist_items=["Step one"])
        complete_item(tmp_dir, "B001")
        content = (tmp_dir / "brief.md").read_text()
        assert "- [x]" in content

    def test_nonexistent_item_raises(self, tmp_dir):
        create_brief("Task", output_dir=tmp_dir, checklist_items=["Step one"])
        with pytest.raises(ValueError, match="not found"):
            complete_item(tmp_dir, "B999")


class TestGetBriefStatus:
    def test_active_brief(self, tmp_dir):
        create_brief("Task", output_dir=tmp_dir, checklist_items=["A", "B"])
        status = get_brief_status(tmp_dir)
        assert status["status"] == "active"
        assert status["total"] == 2
        assert status["done"] == 0

    def test_partially_done(self, tmp_dir):
        create_brief("Task", output_dir=tmp_dir, checklist_items=["A", "B"])
        complete_item(tmp_dir, "B001")
        status = get_brief_status(tmp_dir)
        assert status["done"] == 1
        assert status["total"] == 2

    def test_all_done(self, tmp_dir):
        create_brief("Task", output_dir=tmp_dir, checklist_items=["A", "B"])
        complete_item(tmp_dir, "B001")
        complete_item(tmp_dir, "B002")
        status = get_brief_status(tmp_dir)
        assert status["status"] == "completed"
        assert status["done"] == 2

    def test_no_brief(self, tmp_dir):
        status = get_brief_status(tmp_dir)
        assert status["status"] == "none"

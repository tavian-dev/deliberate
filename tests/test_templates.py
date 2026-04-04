"""Tests for template loading and rendering."""

import tempfile
from pathlib import Path

import pytest
from deliberate.templates import load_template, render_template, find_templates_dir, find_step_guide


class TestFindTemplatesDir:
    def test_defaults_to_package(self):
        tdir = find_templates_dir()
        assert tdir.is_dir()

    def test_prefers_project_local(self):
        with tempfile.TemporaryDirectory() as d:
            local = Path(d) / ".deliberate" / "templates"
            local.mkdir(parents=True)
            (local / "brief.md").write_text("# Brief")
            tdir = find_templates_dir(Path(d))
            assert str(tdir) == str(local)


class TestLoadTemplate:
    def test_loads_default_template(self):
        content = load_template("brief")
        assert len(content) > 0

    def test_missing_template_raises(self):
        with pytest.raises(FileNotFoundError):
            load_template("nonexistent_template_xyz")


class TestRenderTemplate:
    def test_renders_variables(self):
        with tempfile.TemporaryDirectory() as d:
            tdir = Path(d)
            (tdir / "test.md").write_text("# ${title}\n\n${description}")
            result = render_template("test", {"title": "My Task", "description": "Do stuff"}, tdir)
            assert "My Task" in result
            assert "Do stuff" in result

    def test_missing_variables_stay(self):
        with tempfile.TemporaryDirectory() as d:
            tdir = Path(d)
            (tdir / "test.md").write_text("# ${title}\n\n${missing}")
            result = render_template("test", {"title": "Present"}, tdir)
            assert "Present" in result
            assert "${missing}" in result  # safe_substitute leaves missing vars


class TestFindStepGuide:
    def test_finds_spec_guide(self):
        path = find_step_guide("spec")
        assert path.exists()
        assert "spec" in path.name

    def test_finds_all_step_guides(self):
        for step in ["brief", "spec", "plan", "tasks", "research"]:
            path = find_step_guide(step)
            assert path.exists(), f"Missing step guide: {step}"

    def test_guide_contains_next_step(self):
        content = find_step_guide("spec").read_text()
        assert "plan" in content.lower()  # spec guide should mention next step

    def test_missing_guide_raises(self):
        with pytest.raises(FileNotFoundError):
            find_step_guide("nonexistent_step_xyz")

    def test_prefers_project_local(self):
        with tempfile.TemporaryDirectory() as d:
            local = Path(d) / "steps"
            local.mkdir(parents=True)
            (local / "spec.md").write_text("# Custom spec guide")
            path = find_step_guide("spec", Path(d))
            assert "Custom" in path.read_text()

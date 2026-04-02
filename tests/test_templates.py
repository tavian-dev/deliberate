"""Tests for template loading and rendering."""

import tempfile
from pathlib import Path

import pytest
from deliberate.templates import load_template, render_template, find_templates_dir


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

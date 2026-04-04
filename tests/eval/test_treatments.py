"""Tests for treatment prompt rendering."""

import pytest
from deliberate_eval import Task, Treatment
from deliberate_eval.treatments import load_template, render_prompt


class TestLoadTemplate:
    def test_class_a(self):
        template = load_template(Treatment.CLASS_A)
        assert "${description}" in template
        assert "${test_command}" in template

    def test_class_b(self):
        template = load_template(Treatment.CLASS_B)
        assert "${description}" in template
        assert "plan" in template.lower() or "checklist" in template.lower()

    def test_missing_template(self):
        with pytest.raises(FileNotFoundError):
            load_template(Treatment.CLASS_C)


class TestRenderPrompt:
    def _task(self, **kwargs):
        defaults = dict(
            id="t1", description="Fix the bug in foo.py",
            repo="owner/repo", test_command="pytest tests/",
        )
        defaults.update(kwargs)
        return Task(**defaults)

    def test_class_a_basic(self):
        task = self._task()
        prompt = render_prompt(Treatment.CLASS_A, task)
        assert "Fix the bug in foo.py" in prompt
        assert "pytest tests/" in prompt
        assert "${" not in prompt  # No unsubstituted vars

    def test_class_b_basic(self):
        task = self._task()
        prompt = render_prompt(Treatment.CLASS_B, task)
        assert "Fix the bug in foo.py" in prompt
        assert "pytest tests/" in prompt

    def test_setup_instructions(self):
        task = self._task(setup_command="pip install -e .")
        prompt = render_prompt(Treatment.CLASS_A, task)
        assert "pip install -e ." in prompt

    def test_no_setup(self):
        task = self._task(setup_command="")
        prompt = render_prompt(Treatment.CLASS_A, task)
        # Should not contain setup block
        assert "Setup:" not in prompt

    def test_multiline_description(self):
        task = self._task(description="Line 1\nLine 2\nLine 3")
        prompt = render_prompt(Treatment.CLASS_A, task)
        assert "Line 1\nLine 2\nLine 3" in prompt

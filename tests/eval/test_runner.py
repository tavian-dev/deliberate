"""Tests for the eval runner."""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from deliberate_eval import Task, Run, Trajectory, Treatment, AgentType
from deliberate_eval.runner import (
    _run_setup, _run_tests, _capture_diff, run_single,
)


class TestRunSetup:
    def test_empty_command(self, tmp_path):
        result = _run_setup(tmp_path, "", tmp_path)
        assert result is None

    def test_success(self, tmp_path):
        result = _run_setup(tmp_path, "echo hello", tmp_path)
        assert result is None

    def test_failure(self, tmp_path):
        result = _run_setup(tmp_path, "false", tmp_path)
        assert result is not None
        assert "Setup failed" in result

    def test_eval_dir_substitution(self, tmp_path):
        # Create a file to verify $EVAL_DIR is substituted
        (tmp_path / "marker.txt").write_text("ok")
        result = _run_setup(
            tmp_path,
            f"cat $EVAL_DIR/marker.txt",
            tmp_path,
        )
        assert result is None


class TestRunTests:
    def test_passing(self, tmp_path):
        passed, output = _run_tests(tmp_path, "true")
        assert passed is True

    def test_failing(self, tmp_path):
        passed, output = _run_tests(tmp_path, "false")
        assert passed is False

    def test_output_captured(self, tmp_path):
        passed, output = _run_tests(tmp_path, "echo 'test output'")
        assert "test output" in output


class TestCaptureDiff:
    def test_no_changes(self, tmp_path):
        # Init a git repo with no changes
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init", "-q"],
                       cwd=tmp_path, check=True, capture_output=True,
                       env={**__import__("os").environ,
                            "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t",
                            "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t"})
        files, added, removed = _capture_diff(tmp_path)
        assert files == []
        assert added == 0
        assert removed == 0

    def test_with_changes(self, tmp_path):
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True,
                       capture_output=True)
        env = {**__import__("os").environ,
               "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t"}
        (tmp_path / "file.txt").write_text("line1\n")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "-m", "init", "-q"],
                       cwd=tmp_path, check=True, capture_output=True, env=env)
        # Make a change
        (tmp_path / "file.txt").write_text("line1\nline2\n")
        files, added, removed = _capture_diff(tmp_path)
        assert "file.txt" in files
        assert added >= 1


class TestRunSingle:
    """Integration-style tests with mocked agent."""

    def _task(self):
        return Task(
            id="test-1",
            description="Fix the test",
            repo="owner/repo",
            test_command="true",  # Always passes
            repo_ref="main",
        )

    @patch("deliberate_eval.runner._clone_repo")
    @patch("deliberate_eval.runner.AGENT_RUNNERS")
    def test_basic_flow(self, mock_runners, mock_clone, tmp_path):
        """Test the runner flow with mocked clone and agent."""
        # Mock clone to just init a git repo
        def fake_clone(repo, dest, ref):
            dest.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "-q"], cwd=dest, check=True,
                           capture_output=True)
            env = {**__import__("os").environ,
                   "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t",
                   "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t"}
            subprocess.run(["git", "commit", "--allow-empty", "-m", "init", "-q"],
                           cwd=dest, check=True, capture_output=True, env=env)

        mock_clone.side_effect = fake_clone

        # Mock agent to return a trajectory
        mock_agent = MagicMock(return_value=Trajectory(
            input_tokens=1000, output_tokens=200,
            total_cost_usd=0.05, duration_ms=5000,
        ))
        mock_runners.__getitem__ = MagicMock(return_value=mock_agent)

        run = run_single(
            task=self._task(),
            treatment=Treatment.CLASS_A,
            agent=AgentType.CLAUDE,
            use_venv=False,
        )

        assert run.status == "completed"
        assert run.trajectory.input_tokens == 1000
        assert run.trajectory.passed is True  # test_command is "true"
        assert run.treatment == "class_a"
        mock_agent.assert_called_once()

    @patch("deliberate_eval.runner._clone_repo")
    @patch("deliberate_eval.runner.AGENT_RUNNERS")
    def test_setup_failure(self, mock_runners, mock_clone, tmp_path):
        """Test that setup failures are captured."""
        def fake_clone(repo, dest, ref):
            dest.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "-q"], cwd=dest, check=True,
                           capture_output=True)

        mock_clone.side_effect = fake_clone

        task = self._task()
        task.setup_command = "exit 1"  # Fails

        run = run_single(
            task=task,
            treatment=Treatment.CLASS_A,
            agent=AgentType.CLAUDE,
            use_venv=False,
        )

        assert run.status == "failed"
        assert "Setup failed" in run.trajectory.error

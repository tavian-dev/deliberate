"""Tests for git worktree management."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from deliberate.worktree import (
    create_worktree, merge_worktree, cleanup_worktree, list_worktrees,
    WorktreeError,
)


@pytest.fixture
def git_repo():
    """Create a temporary git repo with an initial commit."""
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
        (repo / "README.md").write_text("# Test Repo")
        subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial", "--no-gpg-sign"], cwd=repo, capture_output=True)
        yield repo


class TestCreateWorktree:
    def test_creates_worktree_dir(self, git_repo):
        wt_path = create_worktree(git_repo, "feature-branch")
        assert wt_path.is_dir()
        assert (wt_path / "README.md").exists()

    def test_worktree_on_separate_branch(self, git_repo):
        wt_path = create_worktree(git_repo, "feature-branch")
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=wt_path, capture_output=True, text=True
        )
        assert result.stdout.strip() == "feature-branch"

    def test_changes_in_worktree_isolated(self, git_repo):
        wt_path = create_worktree(git_repo, "feature-branch")
        (wt_path / "new_file.txt").write_text("hello")
        # Main repo should not have the file
        assert not (git_repo / "new_file.txt").exists()

    def test_duplicate_branch_raises(self, git_repo):
        create_worktree(git_repo, "feature-branch")
        with pytest.raises(WorktreeError, match="already exists"):
            create_worktree(git_repo, "feature-branch")


class TestMergeWorktree:
    def test_clean_merge(self, git_repo):
        wt_path = create_worktree(git_repo, "feature-branch")
        # Make a change in the worktree
        (wt_path / "feature.txt").write_text("new feature")
        subprocess.run(["git", "add", "-A"], cwd=wt_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add feature", "--no-gpg-sign"],
                       cwd=wt_path, capture_output=True)
        # Merge back
        result = merge_worktree(git_repo, "feature-branch")
        assert result["status"] == "merged"
        assert (git_repo / "feature.txt").exists()

    def test_conflict_detection(self, git_repo):
        wt_path = create_worktree(git_repo, "feature-branch")
        # Change same file in both
        (git_repo / "README.md").write_text("# Changed in main")
        subprocess.run(["git", "add", "-A"], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "main change", "--no-gpg-sign"],
                       cwd=git_repo, capture_output=True)
        (wt_path / "README.md").write_text("# Changed in feature")
        subprocess.run(["git", "add", "-A"], cwd=wt_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "feature change", "--no-gpg-sign"],
                       cwd=wt_path, capture_output=True)
        result = merge_worktree(git_repo, "feature-branch")
        assert result["status"] == "conflict"
        assert len(result["conflicting_files"]) > 0

    def test_merge_nonexistent_raises(self, git_repo):
        with pytest.raises(WorktreeError, match="not found"):
            merge_worktree(git_repo, "nonexistent-branch")


class TestCleanupWorktree:
    def test_removes_worktree(self, git_repo):
        wt_path = create_worktree(git_repo, "feature-branch")
        assert wt_path.is_dir()
        cleanup_worktree(git_repo, "feature-branch")
        assert not wt_path.is_dir()

    def test_cleanup_nonexistent_is_safe(self, git_repo):
        # Should not raise
        cleanup_worktree(git_repo, "nonexistent-branch")


class TestListWorktrees:
    def test_lists_main(self, git_repo):
        wts = list_worktrees(git_repo)
        assert len(wts) >= 1

    def test_lists_created_worktree(self, git_repo):
        create_worktree(git_repo, "feature-branch")
        wts = list_worktrees(git_repo)
        branches = [wt.get("branch", "") for wt in wts]
        assert any("feature-branch" in b for b in branches)

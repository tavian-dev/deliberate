"""Git worktree management for parallel implementation.

Creates isolated git worktrees for independent phases of a campaign,
allowing parallel work that merges back cleanly.
"""

import subprocess
from pathlib import Path
from typing import Optional


class WorktreeError(Exception):
    """Error during worktree operations."""
    pass


def _git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd, capture_output=True, text=True, timeout=30
    )
    if check and result.returncode != 0:
        raise WorktreeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result


def create_worktree(repo_dir: Path, branch_name: str) -> Path:
    """Create an isolated git worktree on a new branch.

    Args:
        repo_dir: Path to the main repository
        branch_name: Name for the new branch

    Returns:
        Path to the worktree directory

    Raises:
        WorktreeError: If branch already exists or git fails
    """
    # Check if branch already exists
    result = _git(["branch", "--list", branch_name], repo_dir, check=False)
    if branch_name in result.stdout:
        raise WorktreeError(f"Branch '{branch_name}' already exists")

    # Check if worktree already exists
    wt_path = repo_dir / ".worktrees" / branch_name
    if wt_path.exists():
        raise WorktreeError(f"Worktree for '{branch_name}' already exists at {wt_path}")

    wt_path.parent.mkdir(parents=True, exist_ok=True)

    # Create worktree with new branch
    _git(["worktree", "add", "-b", branch_name, str(wt_path)], repo_dir)

    return wt_path


def merge_worktree(repo_dir: Path, branch_name: str) -> dict:
    """Merge a worktree branch back into the current branch.

    Returns dict with:
        status: "merged" | "conflict" | "nothing"
        conflicting_files: list of conflicting file paths (if conflict)
        message: human-readable description
    """
    # Verify branch exists
    result = _git(["branch", "--list", branch_name], repo_dir, check=False)
    if branch_name not in result.stdout:
        raise WorktreeError(f"Branch '{branch_name}' not found")

    # Check if there's anything to merge
    result = _git(["log", f"HEAD..{branch_name}", "--oneline"], repo_dir, check=False)
    if not result.stdout.strip():
        return {"status": "nothing", "conflicting_files": [], "message": "Nothing to merge"}

    # Try the merge
    result = _git(["merge", "--no-edit", branch_name], repo_dir, check=False)

    if result.returncode == 0:
        return {
            "status": "merged",
            "conflicting_files": [],
            "message": f"Successfully merged {branch_name}",
        }

    # Conflict — find conflicting files
    conflict_result = _git(["diff", "--name-only", "--diff-filter=U"], repo_dir, check=False)
    conflicting = [f.strip() for f in conflict_result.stdout.strip().split("\n") if f.strip()]

    # Abort the merge to leave repo clean
    _git(["merge", "--abort"], repo_dir, check=False)

    return {
        "status": "conflict",
        "conflicting_files": conflicting,
        "message": f"Merge conflict in {len(conflicting)} file(s): {', '.join(conflicting)}",
    }


def cleanup_worktree(repo_dir: Path, branch_name: str):
    """Remove a worktree and its branch.

    Safe to call even if worktree doesn't exist.
    """
    wt_path = repo_dir / ".worktrees" / branch_name

    # Remove worktree
    if wt_path.exists():
        _git(["worktree", "remove", str(wt_path), "--force"], repo_dir, check=False)

    # Prune any stale worktrees
    _git(["worktree", "prune"], repo_dir, check=False)

    # Delete branch
    _git(["branch", "-D", branch_name], repo_dir, check=False)


def list_worktrees(repo_dir: Path) -> list[dict]:
    """List all worktrees for the repository."""
    result = _git(["worktree", "list", "--porcelain"], repo_dir, check=False)
    if not result.stdout.strip():
        return []

    worktrees = []
    current = {}
    for line in result.stdout.strip().split("\n"):
        if line.startswith("worktree "):
            if current:
                worktrees.append(current)
            current = {"path": line[len("worktree "):]}
        elif line.startswith("HEAD "):
            current["head"] = line[len("HEAD "):]
        elif line.startswith("branch "):
            current["branch"] = line[len("branch "):]
        elif line == "bare":
            current["bare"] = True
        elif line == "detached":
            current["detached"] = True

    if current:
        worktrees.append(current)

    return worktrees

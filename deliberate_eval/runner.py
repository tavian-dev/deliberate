"""Core eval runner — executes tasks against agents with treatment conditions."""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

from deliberate_eval import Task, Run, Trajectory, Treatment, AgentType
from deliberate_eval.agents import AGENT_RUNNERS
from deliberate_eval.treatments import render_prompt


def _clone_repo(repo: str, dest: Path, ref: str) -> None:
    """Clone a repo and checkout a specific ref."""
    # Check if we already have a local clone we can use
    subprocess.run(
        ["git", "clone", "--quiet", f"https://github.com/{repo}.git", str(dest)],
        check=True, capture_output=True, text=True, timeout=120,
    )
    subprocess.run(
        ["git", "checkout", "-q", ref],
        check=True, capture_output=True, text=True,
        cwd=dest, timeout=30,
    )


def _create_worktree(repo_dir: Path, ref: str, worktree_dir: Path) -> None:
    """Create a git worktree at a specific ref."""
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree_dir), ref],
        check=True, capture_output=True, text=True,
        cwd=repo_dir, timeout=30,
    )


def _cleanup_worktree(repo_dir: Path, worktree_dir: Path) -> None:
    """Remove a git worktree."""
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(worktree_dir)],
        capture_output=True, text=True, cwd=repo_dir, timeout=30,
    )


def _run_setup(workdir: Path, setup_command: str, eval_dir: Path) -> Optional[str]:
    """Run setup command in the workdir. Returns error string or None."""
    if not setup_command:
        return None

    # Substitute $EVAL_DIR
    cmd = setup_command.replace("$EVAL_DIR", str(eval_dir))

    result = subprocess.run(
        ["bash", "-c", cmd],
        capture_output=True, text=True,
        cwd=workdir, timeout=300,
    )
    if result.returncode != 0:
        return f"Setup failed: {result.stderr[:500]}"
    return None


def _run_tests(workdir: Path, test_command: str) -> tuple[bool, str]:
    """Run test command. Returns (passed, output)."""
    result = subprocess.run(
        ["bash", "-c", test_command],
        capture_output=True, text=True,
        cwd=workdir, timeout=120,
    )
    output = result.stdout + result.stderr
    passed = result.returncode == 0
    return passed, output[-2000:]  # Truncate to last 2000 chars


def _capture_diff(workdir: Path) -> tuple[list[str], int, int]:
    """Capture git diff stats. Returns (files_changed, lines_added, lines_removed)."""
    result = subprocess.run(
        ["git", "diff", "--stat", "--numstat"],
        capture_output=True, text=True,
        cwd=workdir, timeout=30,
    )
    files = []
    added = 0
    removed = 0
    for line in result.stdout.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) == 3:
            try:
                added += int(parts[0])
                removed += int(parts[1])
                files.append(parts[2])
            except ValueError:
                continue
    return files, added, removed


def run_single(
    task: Task,
    treatment: Treatment,
    agent: AgentType,
    seed: int = 0,
    eval_dir: Optional[Path] = None,
    clone_dir: Optional[Path] = None,
    agent_timeout: int = 300,
    use_venv: bool = True,
) -> Run:
    """Run a single eval: one task x one treatment x one seed.

    Args:
        task: The task to evaluate.
        treatment: Treatment condition (class_a, class_b, etc.).
        agent: Which agent to use.
        seed: Run seed (for reproducibility tracking).
        eval_dir: Base directory for eval assets (patches, etc.).
        clone_dir: Directory containing pre-cloned repos. If None, clones fresh.
        agent_timeout: Max seconds for agent execution.
        use_venv: Whether to create a venv for setup.

    Returns:
        A completed Run with trajectory data.
    """
    import tempfile

    eval_dir = eval_dir or Path(__file__).parent.parent
    run = Run(
        task_id=task.id,
        treatment=treatment.value,
        agent=agent.value,
        seed=seed,
        status="running",
    )

    workdir = None
    repo_dir = None
    tmpdir = None

    try:
        # 1. Set up working directory
        tmpdir = Path(tempfile.mkdtemp(prefix=f"eval-{task.id}-"))

        if clone_dir and (clone_dir / task.repo.replace("/", "-")).exists():
            # Use pre-cloned repo with worktree
            repo_dir = clone_dir / task.repo.replace("/", "-")
            workdir = tmpdir / "worktree"
            _create_worktree(repo_dir, task.repo_ref, workdir)
        else:
            # Fresh clone
            workdir = tmpdir / "repo"
            _clone_repo(task.repo, workdir, task.repo_ref)

        # 2. Optionally create a venv
        venv_prefix = ""
        if use_venv:
            venv_path = tmpdir / "venv"
            subprocess.run(
                ["python3", "-m", "venv", str(venv_path)],
                check=True, capture_output=True, text=True, timeout=30,
            )
            venv_prefix = f"source {venv_path}/bin/activate && "

        # 3. Run setup (install deps, apply patches)
        setup_cmd = task.setup_command
        if venv_prefix and setup_cmd:
            setup_cmd = venv_prefix + setup_cmd

        setup_error = _run_setup(workdir, setup_cmd, eval_dir)
        if setup_error:
            run.status = "failed"
            run.trajectory = Trajectory(error=setup_error)
            return run

        # 4. Render prompt and invoke agent
        prompt = render_prompt(treatment, task)
        agent_runner = AGENT_RUNNERS[agent]
        trajectory = agent_runner(prompt, workdir, timeout=agent_timeout)

        # 5. Capture diff stats
        files, added, removed = _capture_diff(workdir)
        trajectory.files_changed = files
        trajectory.lines_added = added
        trajectory.lines_removed = removed

        # 6. Run tests
        test_cmd = task.test_command
        if venv_prefix:
            test_cmd = venv_prefix + test_cmd

        passed, test_output = _run_tests(workdir, test_cmd)
        trajectory.passed = passed
        trajectory.test_output = test_output

        run.trajectory = trajectory
        run.status = "completed"

    except Exception as e:
        run.status = "failed"
        run.trajectory = Trajectory(error=f"runner error: {e}")

    finally:
        # Cleanup
        if repo_dir and workdir and workdir.exists():
            _cleanup_worktree(repo_dir, workdir)
        if tmpdir and tmpdir.exists():
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    return run


def run_paired(
    task: Task,
    agent: AgentType = AgentType.CLAUDE,
    seeds: int = 3,
    eval_dir: Optional[Path] = None,
    clone_dir: Optional[Path] = None,
    agent_timeout: int = 300,
) -> list[Run]:
    """Run a paired comparison: class_a vs class_b for a task, N seeds each.

    Returns all runs (2 * seeds total).
    """
    runs = []
    treatments = [Treatment.CLASS_A, Treatment.CLASS_B]

    for seed in range(seeds):
        for treatment in treatments:
            run = run_single(
                task=task,
                treatment=treatment,
                agent=agent,
                seed=seed,
                eval_dir=eval_dir,
                clone_dir=clone_dir,
                agent_timeout=agent_timeout,
            )
            runs.append(run)

    return runs


def run_pilot(
    tasks_path: Path,
    output_path: Path,
    agent: AgentType = AgentType.CLAUDE,
    seeds: int = 3,
    eval_dir: Optional[Path] = None,
    clone_dir: Optional[Path] = None,
    agent_timeout: int = 300,
) -> list[Run]:
    """Run the full pilot eval: all tasks x both treatments x N seeds.

    Writes results to JSONL as they complete. Returns all runs.
    """
    from deliberate_eval.tasks import load_tasks

    tasks = load_tasks(tasks_path)
    all_runs = []

    output_path.parent.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        runs = run_paired(
            task=task,
            agent=agent,
            seeds=seeds,
            eval_dir=eval_dir,
            clone_dir=clone_dir,
            agent_timeout=agent_timeout,
        )
        all_runs.extend(runs)

        # Write results incrementally
        with output_path.open("a") as f:
            for run in runs:
                f.write(run.to_jsonl() + "\n")

    return all_runs

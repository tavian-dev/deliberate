"""Task loading and validation."""

import json
import subprocess
from pathlib import Path

from deliberate_eval import Task


def load_tasks(path: Path) -> list[Task]:
    """Load tasks from a JSONL file. Each line is one task."""
    tasks = []
    for line in path.read_text().strip().split("\n"):
        if not line.strip():
            continue
        d = json.loads(line)
        tasks.append(Task.from_dict(d))
    return tasks


def save_tasks(tasks: list[Task], path: Path) -> None:
    """Save tasks to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(t.to_dict()) for t in tasks]
    path.write_text("\n".join(lines) + "\n")


def append_task(task: Task, path: Path) -> None:
    """Append a single task to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(task.to_dict()) + "\n")


def validate_task(task: Task) -> list[str]:
    """Validate a task has required fields. Returns list of errors."""
    errors = []
    if not task.id:
        errors.append("Task missing 'id'")
    if not task.description:
        errors.append(f"Task {task.id}: missing 'description'")
    if not task.repo:
        errors.append(f"Task {task.id}: missing 'repo'")
    if not task.test_command:
        errors.append(f"Task {task.id}: missing 'test_command'")
    if task.difficulty not in ("trivial", "medium", "hard"):
        errors.append(f"Task {task.id}: invalid difficulty '{task.difficulty}'")
    return errors


def fetch_github_issue(owner_repo: str, issue_number: int) -> dict:
    """Fetch issue details from GitHub using gh CLI. Returns dict with title, body, url."""
    result = subprocess.run(
        ["gh", "api", f"repos/{owner_repo}/issues/{issue_number}",
         "--jq", '{title: .title, body: .body, url: .html_url, state: .state}'],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch issue: {result.stderr.strip()}")
    return json.loads(result.stdout)


def task_from_issue(
    owner_repo: str,
    issue_number: int,
    test_command: str,
    difficulty: str = "medium",
    repo_ref: str = "",
    setup_command: str = "",
    task_id: str = "",
) -> Task:
    """Create a Task from a GitHub issue."""
    issue = fetch_github_issue(owner_repo, issue_number)
    if not task_id:
        task_id = f"{owner_repo.replace('/', '-')}-{issue_number}"
    description = f"{issue['title']}\n\n{issue['body'] or ''}"
    return Task(
        id=task_id,
        description=description.strip(),
        repo=owner_repo,
        test_command=test_command,
        difficulty=difficulty,
        issue_url=issue["url"],
        repo_ref=repo_ref or "main",
        setup_command=setup_command,
    )

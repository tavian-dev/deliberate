"""Task loading and validation."""

import json
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

"""Process runners for each weight class.

Class A: No artifacts, just verification after completion.
Class B: Brief with checklist and done criteria.
Class C/D: Full pipeline (spec → plan → tasks) — implemented later.
"""

import re
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Optional

from deliberate import Brief, CheckItem


# --- Brief (Class B) ---

def _extract_checklist_from_description(description: str) -> list[str]:
    """Extract actionable items from a task description.

    Looks for: comma-separated clauses, colon-separated lists,
    and individual sentences that sound like action items.
    """
    items = []

    # Check for explicit list after colon
    if ":" in description:
        _, _, after_colon = description.partition(":")
        parts = re.split(r"[,;]", after_colon)
        items = [p.strip() for p in parts if len(p.strip()) > 3]

    # If no explicit list, break into sentences/clauses
    if not items:
        parts = re.split(r"[.,;]", description)
        items = [p.strip() for p in parts if len(p.strip()) > 5]

    # If still nothing, use the whole description as one item
    if not items:
        items = [description.strip()]

    return items[:10]  # Cap at 10 items


def create_brief(
    description: str,
    output_dir: Path,
    checklist_items: Optional[list[str]] = None,
    done_criteria: Optional[str] = None,
) -> Brief:
    """Create a Class B brief with checklist.

    Args:
        description: Task description
        output_dir: Directory to write brief.md
        checklist_items: Explicit checklist items (auto-extracted if None)
        done_criteria: Explicit done criteria (auto-generated if None)

    Returns:
        Brief object with checklist
    """
    # Build checklist
    raw_items = checklist_items or _extract_checklist_from_description(description)
    checklist = [
        CheckItem(id=f"B{i+1:03d}", description=item)
        for i, item in enumerate(raw_items)
    ]

    # Generate done criteria if not provided
    if not done_criteria:
        done_criteria = f"All {len(checklist)} checklist items completed and verified."

    brief = Brief(
        title=description.split(":")[0].strip() if ":" in description else description,
        description=description,
        checklist=checklist,
        done_criteria=done_criteria,
        status="active",
    )

    # Write to file
    _write_brief(brief, output_dir)

    return brief


def _write_brief(brief: Brief, output_dir: Path):
    """Write brief to markdown file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    checklist_lines = []
    for item in brief.checklist:
        mark = "x" if item.done else " "
        checklist_lines.append(f"- [{mark}] [{item.id}] {item.description}")

    content = f"""# Brief: {brief.title}

**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Status**: {brief.status}

## Task

{brief.description}

## Checklist

{chr(10).join(checklist_lines)}

## Done When

{brief.done_criteria}
"""
    (output_dir / "brief.md").write_text(content)


def _parse_brief(output_dir: Path) -> Optional[Brief]:
    """Parse brief.md back into a Brief object."""
    path = output_dir / "brief.md"
    if not path.exists():
        return None

    content = path.read_text()
    lines = content.split("\n")

    # Extract title
    title = ""
    for line in lines:
        if line.startswith("# Brief:"):
            title = line[len("# Brief:"):].strip()
            break

    # Extract status
    status = "active"
    for line in lines:
        if line.startswith("**Status**:"):
            status = line.split(":", 1)[1].strip()
            break

    # Extract checklist items
    checklist = []
    for line in lines:
        match = re.match(r"- \[([ x])\] \[([A-Z]\d+)\] (.+)", line)
        if match:
            done = match.group(1) == "x"
            item_id = match.group(2)
            desc = match.group(3)
            checklist.append(CheckItem(id=item_id, description=desc, done=done))

    # Extract description (between ## Task and ## Checklist)
    description = ""
    in_task = False
    for line in lines:
        if line.startswith("## Task"):
            in_task = True
            continue
        if line.startswith("## ") and in_task:
            break
        if in_task and line.strip():
            description = line.strip()

    # Extract done criteria
    done_criteria = ""
    in_done = False
    for line in lines:
        if line.startswith("## Done When"):
            in_done = True
            continue
        if in_done and line.strip():
            done_criteria = line.strip()
            break

    return Brief(
        title=title,
        description=description,
        checklist=checklist,
        done_criteria=done_criteria,
        status=status,
    )


def complete_item(output_dir: Path, item_id: str) -> Brief:
    """Mark a checklist item as done and update the file.

    Raises ValueError if item_id not found.
    """
    brief = _parse_brief(output_dir)
    if brief is None:
        raise FileNotFoundError(f"No brief.md found in {output_dir}")

    found = False
    for item in brief.checklist:
        if item.id == item_id:
            item.done = True
            found = True
            break

    if not found:
        raise ValueError(f"Item {item_id} not found in brief")

    # Check if all done
    if all(item.done for item in brief.checklist):
        brief.status = "completed"

    _write_brief(brief, output_dir)
    return brief


def get_brief_status(output_dir: Path) -> dict:
    """Get the status of a brief."""
    brief = _parse_brief(output_dir)
    if brief is None:
        return {"status": "none", "total": 0, "done": 0}

    total = len(brief.checklist)
    done = sum(1 for item in brief.checklist if item.done)

    return {
        "status": "completed" if done == total else brief.status,
        "total": total,
        "done": done,
        "items": [
            {"id": item.id, "description": item.description, "done": item.done}
            for item in brief.checklist
        ],
    }

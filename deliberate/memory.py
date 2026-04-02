"""Plan outcome memory and recall integration.

Records plan outcomes as searchable markdown files.
Optionally integrates with recall for semantic search.
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from deliberate import WeightClass


def _outcomes_dir(base_dir: Path) -> Path:
    return base_dir / ".deliberate" / "outcomes"


VALID_OUTCOMES = ("success", "partial", "failure", "abandoned")


def record_outcome(
    task: str,
    weight_class: WeightClass,
    outcome: str,
    base_dir: Path = Path("."),
    surprises: Optional[list[str]] = None,
    duration_minutes: Optional[int] = None,
    escalated_from: Optional[WeightClass] = None,
):
    """Record a plan outcome as a markdown file."""
    if outcome not in VALID_OUTCOMES:
        raise ValueError(f"Invalid outcome '{outcome}'. Must be one of: {VALID_OUTCOMES}")

    out_dir = _outcomes_dir(base_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r"[^a-z0-9]+", "-", task.lower())[:40].strip("-")
    filepath = out_dir / f"{date_str}-{slug}.md"

    # Handle filename collisions
    counter = 1
    while filepath.exists():
        filepath = out_dir / f"{date_str}-{slug}-{counter}.md"
        counter += 1

    # Build frontmatter
    fm_lines = [
        "---",
        f"task: \"{task}\"",
        f"weight_class: {weight_class.value}",
        f"outcome: {outcome}",
        f"date: {date_str}",
    ]
    if escalated_from:
        fm_lines.append(f"escalated_from: {escalated_from.value}")
    if duration_minutes is not None:
        fm_lines.append(f"duration_minutes: {duration_minutes}")
    fm_lines.append("---")

    # Build body
    body_lines = [f"# Outcome: {task}", ""]
    body_lines.append(f"**Result**: {outcome}")
    body_lines.append(f"**Weight class**: {weight_class.value}")
    if escalated_from:
        body_lines.append(f"**Escalated from**: {escalated_from.value}")
    if duration_minutes:
        body_lines.append(f"**Duration**: {duration_minutes} minutes")
    body_lines.append("")

    if surprises:
        body_lines.append("## Surprises")
        for s in surprises:
            body_lines.append(f"- {s}")
        body_lines.append("")

    content = "\n".join(fm_lines) + "\n\n" + "\n".join(body_lines)
    filepath.write_text(content)

    # Try to add to recall if available
    try:
        subprocess.run(
            ["recall", "add", task, "--dir", str(out_dir),
             "--type", "observation", "--confidence", "0.9",
             "--tags", f"outcome,{weight_class.value},{outcome}"],
            capture_output=True, timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # recall not available, that's fine

    return filepath


def search_outcomes(
    query: str,
    base_dir: Path = Path("."),
    limit: int = 5,
) -> list[dict]:
    """Search past outcomes. Uses recall if available, falls back to grep."""
    out_dir = _outcomes_dir(base_dir)
    if not out_dir.is_dir():
        return []

    files = sorted(out_dir.glob("*.md"), reverse=True)
    if not files:
        return []

    # Try recall first
    try:
        result = subprocess.run(
            ["recall", "search", query, "--dir", str(out_dir),
             "-n", str(limit), "-f", "json", "-m", "bm25"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json
            items = json.loads(result.stdout)
            return [{"task": i.get("title", ""), "path": i.get("path", ""),
                     "score": i.get("score", 0)} for i in items]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: simple keyword matching
    query_words = set(query.lower().split())
    results = []
    for f in files[:50]:  # Check last 50 files max
        text = f.read_text()  # Read once, reuse
        content_lower = text.lower()
        matches = sum(1 for w in query_words if w in content_lower)
        if matches > 0:
            # Extract task from frontmatter
            task = ""
            for line in text.split("\n"):
                if line.startswith("task:"):
                    task = line.split(":", 1)[1].strip().strip('"')
                    break
            results.append({"task": task or f.stem, "path": str(f), "score": matches})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def list_outcomes(base_dir: Path = Path(".")) -> list[dict]:
    """List all recorded outcomes."""
    out_dir = _outcomes_dir(base_dir)
    if not out_dir.is_dir():
        return []

    outcomes = []
    for f in sorted(out_dir.glob("*.md"), reverse=True):
        content = f.read_text()
        meta = {}
        for line in content.split("\n"):
            if line.startswith("---"):
                continue
            if ":" in line and not line.startswith("#"):
                key, _, val = line.partition(":")
                key = key.strip()
                val = val.strip().strip('"')
                if key in ("task", "weight_class", "outcome", "date", "duration_minutes"):
                    meta[key] = val
            if line.startswith("# "):
                break  # Past frontmatter

        if meta:
            outcomes.append(meta)

    return outcomes

"""MCP server for deliberate — expose planning tools via Model Context Protocol.

Tools:
  - deliberate_classify: classify task complexity
  - deliberate_brief: create a Class B brief
  - deliberate_brief_status: check brief completion
  - deliberate_escalation: check if weight class should change

Usage:
  claude mcp add deliberate -- python3 /path/to/deliberate/mcp_server.py
"""

from pathlib import Path

from fastmcp import FastMCP

from deliberate import WeightClass
from deliberate.classify import classify, check_escalation, CLASS_ORDER
from deliberate.process import create_brief, get_brief_status

mcp = FastMCP("deliberate")


@mcp.tool()
def deliberate_classify(
    description: str,
    file_count: int = -1,
    familiarity: float = -1.0,
) -> str:
    """Classify a task's complexity into weight class A/B/C/D.

    Args:
        description: Natural language task description
        file_count: Estimated number of files affected (-1 for unknown)
        familiarity: How familiar with this area, 0.0-1.0 (-1 for unknown)
    """
    context = {}
    if file_count >= 0:
        context["file_count"] = file_count
    if familiarity >= 0:
        context["familiarity"] = familiarity

    result = classify(description, context=context or None)

    emoji = {"act": "⚡", "brief": "📋", "campaign": "🏗️", "deliberate": "🔬"}
    e = emoji.get(result.weight_class.value, "")
    return (
        f"{e} Class {result.weight_class.name}: {result.weight_class.value}\n"
        f"Confidence: {result.confidence:.0%}\n"
        f"{result.reasoning}"
    )


@mcp.tool()
def deliberate_classify_json(
    description: str,
    file_count: int = -1,
    familiarity: float = -1.0,
) -> str:
    """Classify task complexity and return structured JSON result.

    Args:
        description: Natural language task description
        file_count: Estimated files affected (-1 for unknown)
        familiarity: Area familiarity 0.0-1.0 (-1 for unknown)
    """
    import json
    context = {}
    if file_count >= 0:
        context["file_count"] = file_count
    if familiarity >= 0:
        context["familiarity"] = familiarity

    result = classify(description, context=context or None)
    return json.dumps({
        "weight_class": result.weight_class.value,
        "confidence": result.confidence,
        "reasoning": result.reasoning,
        "signals": {k: round(v, 3) for k, v in result.signals.items()},
    })


@mcp.tool()
def deliberate_brief(
    description: str,
    output_dir: str = ".",
    checklist_items: str = "",
) -> str:
    """Create a Class B brief with checklist.

    Args:
        description: Task description
        output_dir: Directory to write brief.md
        checklist_items: Comma-separated checklist items (auto-extracted if empty)
    """
    items = [i.strip() for i in checklist_items.split(",") if i.strip()] if checklist_items else None
    brief = create_brief(description, Path(output_dir), checklist_items=items)
    return (
        f"📋 Brief created: {Path(output_dir) / 'brief.md'}\n"
        f"{len(brief.checklist)} items:\n" +
        "\n".join(f"  - [{item.id}] {item.description}" for item in brief.checklist) +
        f"\nDone when: {brief.done_criteria}"
    )


@mcp.tool()
def deliberate_brief_status(output_dir: str = ".") -> str:
    """Check the status of an active brief.

    Args:
        output_dir: Directory containing brief.md
    """
    import json
    status = get_brief_status(Path(output_dir))
    return json.dumps(status, indent=2)


@mcp.tool()
def deliberate_check_escalation(
    current_class: str,
    attempts: int = 1,
    scope_grew: bool = False,
    actual_files: int = -1,
) -> str:
    """Check if the current weight class should change.

    Args:
        current_class: Current class (A, B, C, or D)
        attempts: Number of attempts so far
        scope_grew: Whether scope grew during execution
        actual_files: Actual files affected (-1 for unknown)
    """
    wc_map = {"A": WeightClass.A, "B": WeightClass.B, "C": WeightClass.C, "D": WeightClass.D}
    wc = wc_map.get(current_class.upper())
    if not wc:
        return f"Invalid class: {current_class}. Use A, B, C, or D."

    result = check_escalation(
        wc, attempts=attempts, scope_grew=scope_grew,
        actual_files=actual_files if actual_files >= 0 else None,
    )

    if result is None:
        return "✅ No change recommended. Current weight class is appropriate."

    direction = "⬆️" if CLASS_ORDER.index(result["recommendation"]) > CLASS_ORDER.index(wc) else "⬇️"
    return f"{direction} Recommendation: Class {result['recommendation'].name} ({result['recommendation'].value})\n{result['reason']}"


if __name__ == "__main__":
    mcp.run()

"""Artifact prerequisite enforcement.

Validates that required artifacts exist before allowing
the next step in the planning process.
"""

from pathlib import Path
from typing import Optional

from deliberate import WeightClass


# Required artifacts per weight class and step
PREREQUISITES = {
    WeightClass.A: {},  # No artifacts needed
    WeightClass.B: {},  # Brief is created, not required as prereq
    WeightClass.C: {
        "plan": ["spec.md"],
        "tasks": ["plan.md"],
        "implement": ["tasks.md"],
    },
    WeightClass.D: {
        "spec": ["research.md"],
        "plan": ["spec.md", "research.md"],
        "tasks": ["plan.md"],
        "implement": ["tasks.md"],
    },
}


def check_prerequisites(
    weight_class: WeightClass,
    step: str,
    campaign_dir: Path,
) -> list[str]:
    """Check if prerequisites are met for the given step.

    Returns:
        Empty list if all prerequisites met.
        List of error messages for missing prerequisites.
    """
    reqs = PREREQUISITES.get(weight_class, {}).get(step, [])
    errors = []

    for req in reqs:
        req_path = campaign_dir / req
        if not req_path.exists():
            errors.append(
                f"Missing required artifact: {req} "
                f"(needed before '{step}' for class {weight_class.value}). "
                f"Expected at: {req_path}"
            )

    return errors

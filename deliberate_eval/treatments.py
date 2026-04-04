"""Treatment prompt template loading and rendering."""

import string
from pathlib import Path

from deliberate_eval import Task, Treatment

# Templates directory relative to package
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "treatments"


def load_template(treatment: Treatment) -> str:
    """Load a treatment template file."""
    path = _TEMPLATES_DIR / f"{treatment.value}.md"
    if not path.exists():
        raise FileNotFoundError(f"Treatment template not found: {path}")
    return path.read_text()


def render_prompt(treatment: Treatment, task: Task) -> str:
    """Render a treatment prompt for a given task.

    Substitutes ${description}, ${test_command}, and ${setup_instructions}
    into the treatment template.
    """
    template = load_template(treatment)

    # Build setup instructions block (only if setup_command exists)
    setup_instructions = ""
    if task.setup_command:
        setup_instructions = f"\nSetup: Run the following before starting:\n  {task.setup_command}\n"

    # Use string.Template for ${var} substitution
    tmpl = string.Template(template)
    return tmpl.safe_substitute(
        description=task.description,
        test_command=task.test_command,
        setup_instructions=setup_instructions,
    )

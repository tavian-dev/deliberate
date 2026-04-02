"""Template loading and rendering."""

from pathlib import Path
from string import Template
from typing import Optional


DEFAULT_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def find_templates_dir(project_dir: Optional[Path] = None) -> Path:
    """Find the templates directory, preferring project-local over defaults."""
    if project_dir:
        local = project_dir / ".deliberate" / "templates"
        if local.is_dir():
            return local
    return DEFAULT_TEMPLATES_DIR


def load_template(name: str, templates_dir: Optional[Path] = None) -> str:
    """Load a template by name (without .md extension)."""
    tdir = templates_dir or DEFAULT_TEMPLATES_DIR
    path = tdir / f"{name}.md"
    if not path.exists():
        # Fall back to package defaults
        path = DEFAULT_TEMPLATES_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {name} (searched {tdir} and {DEFAULT_TEMPLATES_DIR})")
    return path.read_text()


def render_template(name: str, variables: dict, templates_dir: Optional[Path] = None) -> str:
    """Load and render a template with variable substitution."""
    content = load_template(name, templates_dir)
    return Template(content).safe_substitute(variables)

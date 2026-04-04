"""deliberate — adaptive planning for autonomous AI agents.

Routes tasks to proportional planning processes based on weight classes.
The agent chooses the right class; deliberate enforces the process.
"""

from dataclasses import dataclass, field
from enum import Enum


class WeightClass(Enum):
    """Task complexity weight classes."""
    A = "act"        # Trivial, reversible, familiar → just do it
    B = "brief"      # Bounded, one-session → checklist then do
    C = "campaign"   # Multi-session, cross-domain → full pipeline
    D = "deliberate" # Uncertain, high-stakes → research + spike + pipeline


@dataclass
class CheckItem:
    """Single item in a brief's checklist."""
    id: str
    description: str
    done: bool = False


@dataclass
class Brief:
    """Lightweight planning artifact for Class B tasks."""
    title: str
    description: str
    checklist: list[CheckItem] = field(default_factory=list)
    done_criteria: str = ""
    status: str = "active"  # active, completed, escalated


# Public API
from deliberate.classify import get_guide, check_escalation
from deliberate.enforce import check_prerequisites
from deliberate.worktree import WorktreeError

"""deliberate — adaptive planning for autonomous AI agents.

Classifies task complexity into weight classes and enforces
proportional planning process.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class WeightClass(Enum):
    """Task complexity weight classes."""
    A = "act"        # Trivial, reversible, familiar → just do it
    B = "brief"      # Bounded, one-session → checklist then do
    C = "campaign"   # Multi-session, cross-domain → full pipeline
    D = "deliberate" # Uncertain, high-stakes → research + spike + pipeline


@dataclass
class Classification:
    """Result of classifying a task's complexity."""
    task_description: str
    weight_class: WeightClass
    confidence: float  # 0.0-1.0
    reasoning: str
    signals: dict = field(default_factory=dict)
    context: dict = field(default_factory=dict)


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
from deliberate.classify import classify
from deliberate.enforce import check_prerequisites
from deliberate.worktree import WorktreeError

"""deliberate-eval — measure whether AI planning tools improve agent outcomes."""

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class Treatment(Enum):
    """Planning treatment levels."""
    CLASS_A = "class_a"  # No planning — just do it
    CLASS_B = "class_b"  # Brief with checklist
    CLASS_C = "class_c"  # Full campaign (spec → plan → tasks)


class AgentType(Enum):
    """Supported agent types."""
    CLAUDE = "claude"
    CODEX = "codex"


@dataclass
class Task:
    """A coding task to evaluate."""
    id: str
    description: str
    repo: str              # owner/repo or local path
    test_command: str       # command to verify success
    difficulty: str = "medium"  # trivial, medium, hard
    issue_url: str = ""
    repo_ref: str = "main"  # git ref to check out
    setup_command: str = ""  # optional setup before agent runs

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Trajectory:
    """Captured metrics from a single agent run."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    total_cost_usd: float = 0.0
    duration_ms: int = 0
    num_turns: int = 0
    files_changed: list[str] = field(default_factory=list)
    lines_added: int = 0
    lines_removed: int = 0
    passed: bool = False
    test_output: str = ""
    error: str = ""

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict:
        d = asdict(self)
        d["total_tokens"] = self.total_tokens
        return d


@dataclass
class Run:
    """A single eval run: one task × one treatment × one seed."""
    task_id: str
    treatment: str
    agent: str
    seed: int = 0
    trajectory: Trajectory = field(default_factory=Trajectory)
    status: str = "pending"  # pending, running, completed, failed

    def to_dict(self) -> dict:
        d = asdict(self)
        d["trajectory"]["total_tokens"] = self.trajectory.total_tokens
        return d

    def to_jsonl(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, d: dict) -> "Run":
        traj_data = d.pop("trajectory", {})
        traj_data.pop("total_tokens", None)  # computed property
        traj = Trajectory(**{k: v for k, v in traj_data.items() if k in Trajectory.__dataclass_fields__})
        return cls(trajectory=traj, **{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

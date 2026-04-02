# Data Model: Adaptive Planning System

## Core Entities

### WeightClass (Enum)
```
A = "act"       # Trivial, reversible, familiar → just do it
B = "brief"     # Bounded, one-session → checklist then do
C = "campaign"  # Multi-session, cross-domain → full pipeline
D = "deliberate" # Uncertain, high-stakes → research + spike + pipeline
```

### Classification
```
task_description: str        # Natural language description
context: dict                # Optional: file_count, area_familiarity, reversibility
weight_class: WeightClass    # Assigned class
confidence: float            # 0.0-1.0
reasoning: str               # Human-readable explanation
signals: dict                # Individual signal scores that led to classification
```

### Brief (Class B artifact)
```
title: str
created: datetime
status: "active" | "completed" | "escalated"
checklist: list[CheckItem]
done_criteria: str
completed_at: datetime | None
```

### CheckItem
```
id: str                      # B001, B002, etc.
description: str
done: bool
```

### Campaign (Class C/D artifact container)
```
name: str                    # e.g., "001-adaptive-planning"
weight_class: WeightClass    # C or D
status: "specifying" | "planning" | "tasking" | "implementing" | "reviewing" | "completed" | "abandoned"
spec: Path | None            # spec.md
plan: Path | None            # plan.md
tasks: Path | None           # tasks.md
research: Path | None        # research.md (D only)
spike: Path | None           # spike.md (D only)
created: datetime
completed_at: datetime | None
```

### Outcome (Memory record)
```
task_description: str
weight_class: WeightClass
weight_class_correct: bool   # Was the classification right in hindsight?
outcome: "success" | "partial" | "failure" | "abandoned"
surprises: list[str]         # Things that were unexpected
duration_minutes: int
escalated: bool              # Did it escalate mid-process?
original_class: WeightClass | None  # If escalated, what was the original class?
recorded_at: datetime
```

## Relationships

```
Classification --assigns--> WeightClass
WeightClass --determines--> Process (A: none, B: brief, C: campaign, D: campaign+research)
Campaign --contains--> [spec.md, plan.md, tasks.md, ...]
Outcome --records--> completed Campaign or Brief
Outcome --informs--> future Classifications (via recall search)
```

## Artifact Filesystem Layout

```
.deliberate/
├── templates/           # Editable templates (copied from defaults on init)
│   ├── brief.md
│   ├── spec.md
│   ├── plan.md
│   ├── tasks.md
│   ├── research.md
│   └── verify.md
├── outcomes/            # Plan outcome records (searchable by recall)
│   ├── 2026-04-02-fix-readme-typo.md
│   └── 2026-04-02-redesign-auth.md
└── active/              # Currently active campaigns
    └── 001-adaptive-planning/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

Note: The spec-kit `specs/` directory pattern is used during development of deliberate itself. The `.deliberate/` directory is what deliberate creates in projects that USE it.

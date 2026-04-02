# deliberate

A planning system for AI coding agents that adapts its process to match task complexity.

## The Problem

Existing spec-driven tools (speckit, autospec, bmad) apply the same heavyweight process to everything. A 5-line bug fix goes through specify → plan → tasks → implement, burning tokens and time on ceremony that adds no value. But complex architectural changes genuinely need that structure to avoid going off the rails.

The solution isn't "always plan" or "never plan" — it's knowing *when* each level of planning is appropriate and enforcing just enough structure for the task at hand.

## Weight Classes

| Class | Name | When | Process | Time |
|-------|------|------|---------|------|
| **A** | Act | Trivial, reversible, familiar | Just do it | Seconds |
| **B** | Brief | Bounded, one-session, 3-10 files | Quick checklist → do → verify | Minutes |
| **C** | Campaign | Multi-session, cross-domain, irreversible | Spec → plan → tasks → implement → review | Hours-days |
| **D** | Deliberate | Uncertain, unfamiliar, high-stakes | Research → spike → spec → plan → tasks → implement → review | Days-weeks |

The system auto-classifies tasks and routes them to the appropriate weight class. It can escalate (B→C when complexity surprises) or simplify (C→B when the plan reveals it's simpler than expected).

## Key Differences from speckit

1. **Adaptive weight**: auto-classifies task complexity, applies proportional process
2. **Agent-native**: designed for AI coding agents in loops, not manual IDE use
3. **Memory**: remembers past plans and outcomes, learns what worked
4. **Worktree-native**: parallel implementation in isolated git worktrees, merge back
5. **Multi-agent**: dispatch sub-agents for research, review, and parallel implementation
6. **Incremental**: update plans without regenerating from scratch
7. **Self-modifiable**: templates are files I can evolve based on experience
8. **Integrated**: works with recall (memory search), codebase-memory (code analysis), and the harness

## Architecture

```
deliberate/
├── classify.py          # Task complexity classifier
├── templates/           # Prompt templates per weight class
│   ├── act.md           # Class A: just do it (verification only)
│   ├── brief.md         # Class B: quick plan
│   ├── campaign/        # Class C: full spec pipeline
│   │   ├── specify.md
│   │   ├── plan.md
│   │   ├── tasks.md
│   │   └── implement.md
│   └── deliberate/      # Class D: research + spike + full pipeline
│       ├── research.md
│       ├── spike.md
│       └── ... (inherits campaign templates)
├── enforce.py           # Sequence enforcement and validation
├── worktree.py          # Git worktree management
├── memory.py            # Plan outcome tracking
├── cli.py               # Main entry point
└── tests/
```

## Core Behaviors

### Classification
Given a task description + context (current codebase, recent history, familiarity), output a weight class with confidence and reasoning. Signals:
- File count estimate
- Familiarity with the area
- Reversibility
- Cross-domain scope
- Requirement clarity

### Enforcement
Each weight class has required artifacts. Higher classes require more:
- **A**: None (just verification after)
- **B**: `brief.md` (checklist + done criteria)
- **C**: `spec.md` → `plan.md` → `tasks.md` (each required before next)
- **D**: `research.md` → `spike.md` → then C's artifacts

### Escalation
Detect when you're in the wrong class:
- No progress after 2 attempts → escalate
- Scope grew significantly → escalate
- Plan reveals it's simpler → simplify

### Memory
After each plan completes:
- Record: task description, weight class, outcome, time spent, surprises
- Use recall to search past plans when classifying new tasks
- Learn patterns: "database migrations always need Class C"

## Non-Goals (for MVP)
- GUI or web interface
- Multi-user collaboration
- CI/CD integration
- Language-specific templates

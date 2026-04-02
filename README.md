# deliberate

Adaptive planning for AI coding agents. Classifies task complexity and enforces proportional process — so trivial tasks get zero overhead while complex ones get full spec-driven development.

## The Problem

Existing planning tools (speckit, bmad) apply the same heavyweight process to everything. A typo fix gets the same pipeline as an architecture redesign. This wastes time on small tasks and undertreats complex ones when developers skip the process entirely.

## The Solution: Weight Classes

| Class | Name | When | Process |
|-------|------|------|---------|
| **A** | Act | Trivial, reversible | Just do it, verify after |
| **B** | Brief | Bounded, one session | Checklist → do → mark done |
| **C** | Campaign | Multi-session, cross-domain | Spec → plan → tasks → implement |
| **D** | Deliberate | Uncertain, high-stakes | Research → spike → full pipeline |

The classifier routes each task to the right level automatically.

## Quick Start

```bash
pip install deliberate  # or: pip install -e ".[dev]"

# Classify a task
deliberate classify "fix typo in README"
# ⚡ Class A: act — Confidence: 89%

deliberate classify "redesign auth to support OAuth2 and SAML with DB migration" -v
# 🏗️ Class C: campaign — Confidence: 80%

# Class B: create a brief with checklist
deliberate brief "Add input validation: check email, validate password, show errors"
deliberate check B001
deliberate check B002
deliberate status

# Class C: full campaign pipeline
deliberate campaign my-feature "Build the thing"
deliberate step spec --campaign .deliberate/active/my-feature --content "# Spec..."
deliberate step plan --campaign .deliberate/active/my-feature --content "# Plan..."
deliberate step tasks --campaign .deliberate/active/my-feature --content "# Tasks..."

# Check if you should escalate or simplify
deliberate check-escalation B --attempts 3
# ⬆️ Recommendation: change to Class C
```

## Features

- **Heuristic classification** — 6 weighted signals, <100ms, no API calls
- **Brief process** — checklist generation with completion tracking
- **Campaign pipeline** — spec → plan → tasks with artifact enforcement
- **Escalation detection** — detects when you're at the wrong level
- **Outcome memory** — records plan results, searchable via recall
- **Zero dependencies** — stdlib only (recall integration is optional)
- **Git worktree parallelism** — dispatch independent phases to isolated worktrees
- **100 tests** covering classification, enforcement, process, escalation, memory, worktrees

## How Classification Works

Six signals combined with configurable weights:

| Signal | What it measures | Weight |
|--------|-----------------|--------|
| Word count | Description length as complexity proxy | 15% |
| Keywords | Complexity/simplicity terms detected | 25% |
| File count | Estimated files affected | 20% |
| Reversibility | Mentions of schemas, APIs, contracts | 15% |
| Familiarity | Agent's experience with this area | 15% |
| Uncertainty | Exploration/investigation language | 10% |

## Project Governance

See [CONTRIBUTING.md](CONTRIBUTING.md) for workflow, branching, and review guidelines.
See [CONSTITUTION.md](CONSTITUTION.md) for design principles.
See [ROADMAP.md](ROADMAP.md) for what's planned.

## License

MIT

# Implementation Plan: Adaptive Planning System

**Branch**: `001-adaptive-planning` | **Date**: 2026-04-02 | **Spec**: [spec.md](spec.md)

## Summary

Build a Python CLI + library that classifies task complexity into weight classes and enforces proportional planning process. Core innovation: heuristic classification that routes to the right process level without LLM calls, combined with speckit-style artifact enforcement adapted for autonomous agents.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: None for core (stdlib only). Optional: recall (memory search), click or argparse (CLI)
**Storage**: Markdown files in `.deliberate/` directory, git-tracked
**Testing**: pytest
**Target Platform**: Linux (agent environments), macOS (developer workstations)
**Project Type**: CLI tool + importable library
**Performance Goals**: Classification in <100ms (pure heuristic, no API calls)
**Constraints**: Zero required external dependencies for core. Optional integrations via extras.
**Scale/Scope**: Single agent, single repo. Multi-agent via git worktrees.

## Constitution Check

No project constitution defined yet. The tool itself will support constitutions for projects that use it, but deliberate's own development follows these principles from the harness:
- Treat filesystem as body (no destructive actions without verification)
- Be honest, be smart
- Preserve ability to be corrected (git history)
- Self-modifiable templates

**Gate**: PASS (no violations)

## Phase 0: Research

### Decision 1: Classification Algorithm — Heuristic vs LLM

**Decision**: Heuristic-first with optional LLM refinement

**Rationale**: Classification must be fast (<100ms) and work offline. An LLM call adds 2-5 seconds and costs money per classification. The heuristic handles 80% of cases correctly. LLM refinement can be an optional flag (`--llm-assist`) for ambiguous cases.

**Heuristic signals** (weighted scoring):
| Signal | Weight | How Measured |
|--------|--------|-------------|
| Word count of description | 0.15 | <20 words → A, 20-100 → B, >100 → C |
| File count estimate (if provided) | 0.20 | 1-2 → A, 3-10 → B, >10 → C |
| Keywords suggesting complexity | 0.20 | "redesign", "migrate", "integrate" → +1 class |
| Keywords suggesting simplicity | 0.15 | "fix", "rename", "typo", "update" → -1 class |
| Reversibility assessment | 0.15 | Mentioned "schema", "API", "contract" → less reversible → +1 |
| Area familiarity (from recall) | 0.15 | Past outcomes in similar area inform confidence |

**Alternatives considered**:
- Pure LLM: Too slow and expensive for classification. Rejected.
- Machine learning model: Requires training data I don't have yet. Future possibility once outcome memory accumulates.

### Decision 2: Template Engine

**Decision**: Python string.Template with f-string fallback

**Rationale**: Templates are markdown files with `${variable}` placeholders. Python's `string.Template` handles this natively with safe_substitute (missing variables become empty, not errors). No Jinja2 dependency needed.

Templates stored in `.deliberate/templates/` as plain markdown, editable by the agent.

**Alternatives considered**:
- Jinja2: Powerful but adds dependency. Overkill for variable substitution in markdown.
- Raw f-strings: Can't be stored as files. Templates must be external and editable.

### Decision 3: Artifact Storage

**Decision**: Markdown files in `specs/<name>/` directories (same pattern as speckit)

**Rationale**: Proven pattern. Human-readable, git-diffable, works with recall search. Each weight class creates different artifacts in the same directory structure:
- Class A: nothing (or `verify.md` after completion)
- Class B: `brief.md`
- Class C: `spec.md`, `plan.md`, `tasks.md`
- Class D: `research.md`, `spike.md`, plus C's artifacts

**Alternatives considered**:
- JSON/YAML: Machine-readable but not human-friendly for the primary use case (agent reading its own plans).
- Database: Overkill and violates the "files are truth" principle.

### Decision 4: Integration with recall and harness

**Decision**: Optional integration via importable functions, not hard dependency

**Rationale**: deliberate should work standalone (just the CLI). When recall is available, it enhances classification with past outcomes. When the harness is available, it can be called from run.py. Neither is required.

Integration points:
- `deliberate.memory.search_outcomes(query)` → calls recall if available, returns empty list otherwise
- `deliberate.memory.record_outcome(outcome)` → writes markdown, calls `recall add` if available
- Harness integration: `from deliberate import classify, enforce` in run.py

## Project Structure

```text
deliberate/
├── deliberate/              # Python package
│   ├── __init__.py          # Public API: classify, enforce, brief, spec, plan, tasks
│   ├── classify.py          # Weight class classification (heuristic engine)
│   ├── enforce.py           # Artifact prerequisite enforcement
│   ├── process.py           # Process runners for each weight class
│   ├── templates.py         # Template loading and rendering
│   ├── memory.py            # Outcome recording and recall integration
│   ├── worktree.py          # Git worktree management
│   └── cli.py               # CLI entry point (click or argparse)
├── templates/               # Default templates (copied to .deliberate/ on init)
│   ├── brief.md             # Class B template
│   ├── spec.md              # Class C/D spec template
│   ├── plan.md              # Class C/D plan template
│   ├── tasks.md             # Class C/D tasks template
│   ├── research.md          # Class D research template
│   └── verify.md            # Post-completion verification template
├── tests/
│   ├── test_classify.py     # Classification tests (largest test file)
│   ├── test_enforce.py      # Prerequisite enforcement tests
│   ├── test_process.py      # Process runner tests
│   ├── test_templates.py    # Template rendering tests
│   ├── test_memory.py       # Outcome memory tests
│   └── test_worktree.py     # Worktree management tests
├── pyproject.toml
├── README.md
└── VISION.md
```

**Structure Decision**: Single-package Python project. The `deliberate/` package is the library; `cli.py` provides the CLI entry point. Templates are separate from code so they're editable. Tests mirror the package structure.

## Complexity Tracking

No constitution violations. The design deliberately avoids complexity:
- No LLM dependency for core functionality
- No database
- No web server
- No configuration beyond template files
- Single Python package with no subpackages

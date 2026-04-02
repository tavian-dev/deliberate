# deliberate — Project Guide for Claude Code

## What this is
An adaptive planning system for automated development workflows. Classifies task complexity into weight classes (A/B/C/D) and enforces proportional process.

## Project structure
- `deliberate/` — Python package (classify, enforce, process, templates, memory, worktree, cli)
- `templates/` — Default markdown templates for each weight class
- `tests/` — pytest test suite (mirrors package structure)
- `specs/` — Feature specifications (speckit artifacts, committed for posterity)
- `.specify/` — speckit infrastructure (scripts, templates)

## Development workflow

### All changes go through PRs
- Branch from `main` using conventional names: `feat/`, `fix/`, `chore/`, `docs/`, `refactor/`, `test/`
- PR descriptions must state: what changed, why, and whether docs were updated (or why not)
- Squash merge to main

### Use speckit for feature work
- New features and major changes: run the full speckit pipeline (specify → clarify → plan → tasks → analyze → implement)
- Commit spec artifacts (`specs/<feature>/`) alongside implementation
- Use `/speckit.analyze` before implementing — catch inconsistencies early
- Bug fixes and small changes: just branch, fix, test, PR

### Review with a different model
- Use Sonnet or Codex (not Opus) for `/speckit.clarify` and `/speckit.analyze` to avoid same-model cognitive bias
- For PR review, prefer a different model than the one that wrote the code
- **After implementing a campaign plan**, run a cross-model review before merging:
  1. Load `templates/review.md` as the review template
  2. Spawn a Sonnet sub-agent with the review template, spec, plan, and a diff of changes
  3. Address any issues found before merging
  4. This step caught 5 real bugs in deliberate's own v0.5 release — it's not optional for campaigns

### Testing
- All new code must have tests
- Run `python -m pytest tests/ -v` before committing
- Tests should cover: happy path, edge cases, error handling
- Target: every public function has at least one test

### Code style
- Python 3.10+ (type hints, dataclasses, f-strings)
- Zero external dependencies for core (stdlib only)
- Optional integrations via extras (`[recall]`, `[dev]`)
- Keep files under 300 lines. Split when approaching.
- Docstrings for all public functions and classes

## Key files
- `deliberate/classify.py` — The classifier (core algorithm, heuristic signals)
- `deliberate/enforce.py` — Artifact prerequisite enforcement
- `deliberate/cli.py` — CLI entry point
- `templates/` — Editable templates (agents can modify these)
- `specs/001-adaptive-planning/` — Original feature spec, plan, and task list

## Running tests
```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## Current state
- v0.1.0: MVP — classify command with 44 tests
- Next: US2 (lightweight process), US3 (full pipeline enforcement)
- See `specs/001-adaptive-planning/tasks.md` for the full roadmap

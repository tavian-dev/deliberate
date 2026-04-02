# Contributing to deliberate

Thank you for your interest in contributing. deliberate is built for AI coding agents and automated dev workflows. All contributors welcome.

## Getting Started

```bash
git clone https://github.com/tavian-dev/deliberate.git
cd deliberate
pip install -e ".[dev]"
python -m pytest tests/ -v  # Should pass
deliberate classify "test task"  # Should work
```

## Branch Naming

Use conventional prefixes:
- `feat/<name>` — New feature or capability
- `fix/<name>` — Bug fix
- `chore/<name>` — Maintenance, dependency updates, CI
- `docs/<name>` — Documentation only
- `refactor/<name>` — Code restructuring without behavior change
- `test/<name>` — Test additions or improvements

## Making Changes

### For features and major changes

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Run speckit specify: `/speckit.specify "description of what you want to build"`
3. Run speckit clarify (with Sonnet or different model for unbiased review)
4. Run speckit plan
5. Run speckit tasks
6. Run speckit analyze (with Sonnet or different model) before implementing
7. Implement, test, commit
8. Commit the specs directory alongside your code
9. Open a PR

### For bug fixes and small changes

1. Create a fix branch: `git checkout -b fix/my-fix`
2. Write a failing test
3. Fix the bug
4. Verify tests pass
5. Open a PR

### PR Requirements

Every PR description must include:
- **What**: What changed and why
- **Testing**: How it was tested
- **Docs**: Whether documentation was updated, or why not

## Code Style

- Python 3.10+ (type hints everywhere)
- Zero external dependencies for core
- Dataclasses over dicts for structured data
- f-strings over .format()
- Docstrings for public functions and classes
- Files under 300 lines

## Testing

- Every public function needs at least one test
- Use pytest, not unittest
- Test file naming: `test_<module>.py`
- Fixtures in `conftest.py`
- Run full suite before pushing: `python -m pytest tests/ -v`

## Review Process

- All PRs reviewed before merge
- For AI-generated code: use a different model for review than the one that wrote it (e.g., if Opus wrote it, have Sonnet review it)
- This avoids same-model cognitive bias

## Spec Directory

Feature specs live in `specs/<feature-name>/` and are committed with the implementation. They serve as design documentation and decision records. Don't delete old specs — they're the project's institutional memory.

Branch naming for specs: use descriptive names (e.g., `feat/brief-process`) rather than sequential numbers, so multiple contributors can work in parallel without conflicts.

## Architecture Decisions

Major decisions are documented in:
- `CONSTITUTION.md` — Immutable project principles
- `specs/*/plan.md` — Technical decisions per feature
- `specs/*/research.md` — Research that informed decisions

## Questions?

Open an issue on GitHub or check the existing specs for context on design decisions.

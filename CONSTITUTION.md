# Constitution

Project principles for deliberate. These guide all design decisions.

## Core Principles

1. **Proportional process.** The amount of planning should match the task's complexity. A typo fix should have zero overhead. An architecture redesign should have full spec-driven development. The system must make the right choice automatically.

2. **No mandatory external dependencies.** Core functionality (classify, enforce, templates) works with Python stdlib alone. Integrations (recall, harness) are optional extras. An agent without recall should still be able to classify tasks.

3. **Agents first, humans welcome.** The primary user is an AI coding agent. But all artifacts are human-readable markdown, all commands have clear output, and the CLI works for manual use too. Never optimize for machines at the expense of readability.

4. **Templates are data, not code.** Templates are editable markdown files, not hardcoded strings. Any agent or human can modify them without touching Python. Templates stay under 50 lines each.

5. **Files are truth.** State is determined by what files exist, not by databases, caches, or in-memory state. Any agent can resume work by reading the filesystem. git history is the audit trail.

6. **Classification is cheap.** Classification must be fast (<100ms) and free (no API calls). It's a heuristic, not an oracle. Wrong classifications are caught by escalation detection, not prevented by expensive upfront analysis.

7. **Escalation over perfection.** It's better to start at the wrong level and escalate than to spend time finding the perfect level. The system detects stalls and recommends reclassification. Existing artifacts are preserved on escalation, not discarded.

## Design Constraints

- Python 3.10+ for broad compatibility
- Single package, no subpackages (deliberate/)
- Tests for every public function
- All specs committed alongside code (specs/ directory)

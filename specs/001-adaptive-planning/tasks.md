# Tasks: Adaptive Planning System

**Input**: Design documents from `/specs/001-adaptive-planning/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓

**Tests**: Included (TDD approach — this is a tool I'll rely on, correctness matters).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1-US6)

---

## Phase 1: Setup

**Purpose**: Project initialization and package structure

- [ ] T001 Create Python package structure: `deliberate/__init__.py`, `deliberate/classify.py`, `deliberate/enforce.py`, `deliberate/process.py`, `deliberate/templates.py`, `deliberate/memory.py`, `deliberate/worktree.py`, `deliberate/cli.py`
- [ ] T002 Create `pyproject.toml` with project metadata, entry point `deliberate = "deliberate.cli:main"`, optional deps `[recall]` and `[dev]`
- [ ] T003 [P] Create default template files: `templates/brief.md`, `templates/spec.md`, `templates/plan.md`, `templates/tasks.md`, `templates/research.md`, `templates/verify.md`
- [ ] T004 [P] Create `tests/` directory with `conftest.py` (shared fixtures: temp directories, sample tasks, mock recall)
- [ ] T005 [P] Create `.gitignore`, `README.md` (from VISION.md content), `LICENSE` (MIT)

**Checkpoint**: Package structure exists, `pip install -e .` succeeds, `deliberate --help` runs (even if commands aren't implemented)

---

## Phase 2: Foundational (WeightClass Enum + Template Engine)

**Purpose**: Core types and template loading that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Define `WeightClass` enum and `Classification` dataclass in `deliberate/__init__.py` (from data-model.md)
- [ ] T007 Implement template loader in `deliberate/templates.py`: discover `.deliberate/templates/` or fall back to package defaults, load by name, render with `string.Template`
- [ ] T008 Write tests for template loader in `tests/test_templates.py`: template discovery, variable substitution, missing template error, fallback to defaults
- [ ] T009 Implement `deliberate init` CLI command that creates `.deliberate/templates/` directory with default templates copied from package

**Checkpoint**: `WeightClass` enum importable, templates load and render, `deliberate init` creates template directory

---

## Phase 3: User Story 1 — Classify and Route Tasks (Priority: P1) 🎯 MVP

**Goal**: Given a task description, return a weight class with confidence and reasoning

**Independent Test**: `deliberate classify "fix typo in README"` → returns class A. `deliberate classify "redesign auth system"` → returns class C.

### Tests for US1

- [ ] T010 [P] [US1] Write classification tests in `tests/test_classify.py`: trivial tasks → A, bounded tasks → B, complex tasks → C, uncertain tasks → D, ambiguous defaults to B, context shifts classification, confidence scoring
- [ ] T011 [P] [US1] Write tests for keyword detection in `tests/test_classify.py`: simplicity keywords lower class, complexity keywords raise class, domain terms detected

### Implementation for US1

- [ ] T012 [US1] Implement signal extractors in `deliberate/classify.py`: `_score_word_count()`, `_score_keywords()`, `_score_file_count()`, `_score_reversibility()`, `_score_familiarity()`
- [ ] T013 [US1] Implement `classify(description, context=None)` in `deliberate/classify.py`: combine weighted signals, apply heuristic thresholds, return `Classification` with class, confidence, reasoning, signals
- [ ] T014 [US1] Implement `deliberate classify <description>` CLI command in `deliberate/cli.py`: parse args, call classify(), print result as formatted text or JSON (`--json`)
- [ ] T015 [US1] Run tests, verify all pass, ensure trivial/complex/ambiguous cases all classified correctly

**Checkpoint**: `deliberate classify` works end-to-end. Core value proposition validated.

---

## Phase 4: User Story 2 — Lightweight Process (Priority: P1)

**Goal**: Class A gets no overhead, class B gets a brief.md with checklist

**Independent Test**: `deliberate brief "add input validation to login form"` → creates brief.md with checklist items. `deliberate act "fix typo"` → returns verification prompt only.

### Tests for US2

- [ ] T016 [P] [US2] Write brief generation tests in `tests/test_process.py`: brief creates file, brief has checklist items, brief has done criteria, brief can mark items complete
- [ ] T017 [P] [US2] Write enforcement tests in `tests/test_enforce.py`: class A requires nothing, class B requires brief.md, verification template rendered correctly

### Implementation for US2

- [ ] T018 [US2] Implement `Brief` and `CheckItem` dataclasses in `deliberate/process.py` (from data-model.md)
- [ ] T019 [US2] Implement `create_brief(description, template_dir)` in `deliberate/process.py`: load brief template, extract checklist items from description, write brief.md
- [ ] T020 [US2] Implement `deliberate brief <description>` and `deliberate act <description>` CLI commands in `deliberate/cli.py`
- [ ] T021 [US2] Implement brief completion tracking: `deliberate check <item_id>` marks items done in brief.md

**Checkpoint**: Lightweight process works. A-class tasks verified, B-class tasks get briefs.

---

## Phase 5: User Story 3 — Full Spec Pipeline (Priority: P2)

**Goal**: Class C tasks get the full spec → plan → tasks → implement pipeline with artifact enforcement

**Independent Test**: Create a C-class campaign, run through spec → plan → tasks, verify each step gates the next.

### Tests for US3

- [ ] T022 [P] [US3] Write enforcement tests in `tests/test_enforce.py`: plan requires spec, tasks requires plan, implement requires tasks, missing artifacts return clear errors
- [ ] T023 [P] [US3] Write campaign lifecycle tests in `tests/test_process.py`: campaign creation, status tracking, artifact registration, completion

### Implementation for US3

- [ ] T024 [US3] Implement `Campaign` dataclass and campaign directory management in `deliberate/process.py`
- [ ] T025 [US3] Implement artifact enforcement in `deliberate/enforce.py`: `check_prerequisites(weight_class, campaign_dir)` validates required files exist, returns errors for missing
- [ ] T026 [US3] Implement `deliberate spec <description>`, `deliberate plan`, `deliberate tasks` CLI commands that create artifacts from templates and enforce prerequisites
- [ ] T027 [US3] Implement campaign status tracking: update status as artifacts are created, persist in `.deliberate/active/<name>/status.json`

**Checkpoint**: Full C-class pipeline works with enforcement. `deliberate tasks` fails without `plan.md`.

---

## Phase 6: User Story 4 — Mid-Process Escalation (Priority: P2)

**Goal**: Detect when the agent is in the wrong weight class and recommend change

**Independent Test**: Simulate 3 failures on a B-class task, verify escalation recommended.

### Tests for US4

- [ ] T028 [P] [US4] Write escalation detection tests in `tests/test_classify.py`: repeated failures trigger escalation, scope growth triggers escalation, plan reveals simplicity triggers simplification, existing artifacts preserved on escalation

### Implementation for US4

- [ ] T029 [US4] Implement `check_escalation(weight_class, attempts, scope_changes)` in `deliberate/classify.py`: check failure count, scope growth, return recommendation
- [ ] T030 [US4] Implement `deliberate check-status` CLI command that reads current campaign state and reports escalation recommendations
- [ ] T031 [US4] Implement artifact preservation on reclassification: escalating from B to C preserves brief.md alongside new spec.md

**Checkpoint**: Escalation detection works. B→C and C→B transitions tested.

---

## Phase 7: User Story 5 — Plan Outcome Memory (Priority: P3)

**Goal**: Record and search plan outcomes for future classification improvement

**Independent Test**: Complete a campaign, verify outcome recorded, search it when classifying a similar task.

### Tests for US5

- [ ] T032 [P] [US5] Write outcome memory tests in `tests/test_memory.py`: outcome recorded as markdown, outcome searchable, past outcomes influence classification

### Implementation for US5

- [ ] T033 [US5] Implement `record_outcome(campaign, result)` in `deliberate/memory.py`: write markdown to `.deliberate/outcomes/`, call `recall add` if available
- [ ] T034 [US5] Implement `search_outcomes(query)` in `deliberate/memory.py`: call recall if available, fall back to glob+grep if not
- [ ] T035 [US5] Wire outcome search into `classify()`: search for similar past tasks, adjust confidence and reasoning based on past results

**Checkpoint**: Outcome memory works. Classification improves with experience.

---

## Phase 8: User Story 6 — Git Worktree Parallelism (Priority: P3)

**Goal**: Dispatch independent phases to isolated git worktrees, merge back

**Independent Test**: Two independent tasks in worktrees, both complete, merge cleanly.

### Tests for US6

- [ ] T036 [P] [US6] Write worktree management tests in `tests/test_worktree.py`: worktree creation, worktree cleanup, clean merge, conflict detection

### Implementation for US6

- [ ] T037 [US6] Implement `create_worktree(branch_name)` and `merge_worktree(branch_name)` in `deliberate/worktree.py`
- [ ] T038 [US6] Implement `deliberate parallel <phase_ids>` CLI command that dispatches phases to worktrees
- [ ] T039 [US6] Implement conflict detection and reporting when merging worktrees with overlapping changes

**Checkpoint**: Worktree parallelism works for independent phases.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T040 [P] Write comprehensive README.md with usage examples for each weight class
- [ ] T041 [P] Add `--verbose` and `--quiet` flags to all CLI commands
- [ ] T042 Ensure all templates are under 50 lines each (per research.md decision)
- [ ] T043 [P] Run full test suite, verify coverage, add missing edge case tests
- [ ] T044 Publish to GitHub as tavian-dev/deliberate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1
- **Phase 3 (US1 Classify)**: Depends on Phase 2 — **MVP target**
- **Phase 4 (US2 Lightweight)**: Depends on Phase 2, can parallel with Phase 3
- **Phase 5 (US3 Pipeline)**: Depends on Phase 2, can parallel with Phase 3-4
- **Phase 6 (US4 Escalation)**: Depends on Phase 3 (needs classify) and Phase 4/5 (needs process)
- **Phase 7 (US5 Memory)**: Depends on Phase 3 (needs classify) 
- **Phase 8 (US6 Worktrees)**: Depends on Phase 5 (needs campaign management)
- **Phase 9 (Polish)**: Depends on all desired phases complete

### User Story Dependencies

- **US1 (Classify)**: Independent after foundational
- **US2 (Lightweight)**: Independent after foundational (parallel with US1)
- **US3 (Pipeline)**: Independent after foundational (parallel with US1, US2)
- **US4 (Escalation)**: Needs US1 classify + US2/US3 process
- **US5 (Memory)**: Needs US1 classify
- **US6 (Worktrees)**: Needs US3 campaign management

### Within Each User Story

- Tests written FIRST, verified to FAIL
- Core types before functions
- Functions before CLI commands
- Integration last

---

## Implementation Strategy

### MVP (US1 Only): Classify and Route

1. Complete Phase 1: Setup → package installable
2. Complete Phase 2: Foundational → types and templates work
3. Complete Phase 3: US1 → `deliberate classify` works
4. **STOP and VALIDATE**: Classification accuracy on test cases
5. Publish v0.1.0

### v0.2.0: Lightweight Process (US1 + US2)

6. Complete Phase 4: US2 → `deliberate brief` and `deliberate act` work
7. Integrate with harness: classify tasks in run.py
8. Publish v0.2.0

### v0.3.0: Full Pipeline (US1 + US2 + US3)

9. Complete Phase 5: US3 → full spec pipeline with enforcement
10. Publish v0.3.0

### v1.0.0: Complete (All Stories)

11. Complete Phase 6-8: Escalation, memory, worktrees
12. Complete Phase 9: Polish
13. Publish v1.0.0

---

## Summary

| Metric | Count |
|--------|-------|
| Total tasks | 44 |
| Phase 1 (Setup) | 5 |
| Phase 2 (Foundational) | 4 |
| US1 (Classify) — P1 | 6 |
| US2 (Lightweight) — P1 | 6 |
| US3 (Pipeline) — P2 | 6 |
| US4 (Escalation) — P2 | 4 |
| US5 (Memory) — P3 | 4 |
| US6 (Worktrees) — P3 | 4 |
| Polish | 5 |
| Parallelizable tasks | 18 (41%) |
| **MVP scope (US1)** | **15 tasks (Phases 1-3)** |

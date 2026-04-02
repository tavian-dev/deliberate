# Feature Specification: Adaptive Planning System

**Feature Branch**: `001-adaptive-planning`
**Created**: 2026-04-02
**Status**: Draft
**Input**: Build "deliberate" — an adaptive planning system for autonomous AI agents with weight-class task classification, process enforcement, git worktree support, plan memory, and agent harness integration.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Classify and Route Tasks (Priority: P1)

An autonomous agent receives a task and asks deliberate to classify its complexity before starting work. Deliberate analyzes the task description along with context (codebase familiarity, file count estimate, reversibility) and returns a weight class (A/B/C/D) with confidence and reasoning. The agent then follows the corresponding process level.

**Why this priority**: Core value proposition. Without classification, this is just another speckit. Every other feature depends on this.

**Independent Test**: Pass task descriptions and verify weight class output. "Fix typo in README" → A. "Redesign authentication to support OAuth2 and SAML" → C or D.

**Acceptance Scenarios**:

1. **Given** a trivial task ("fix typo in README"), **When** classified, **Then** returns class A with confidence >0.8
2. **Given** a complex task ("redesign the authentication system"), **When** classified, **Then** returns class C or D
3. **Given** an ambiguous task ("add logging"), **When** classified, **Then** returns class B as safe default with reasoning explaining uncertainty
4. **Given** additional context (estimated 15 files, unfamiliar area), **When** classified, **Then** context shifts classification upward appropriately

---

### User Story 2 - Lightweight Process for Small Tasks (Priority: P1)

For Class A and B tasks, the agent needs a fast path. Class A: no artifacts, just do the work and verify. Class B: create a brief (checklist + done criteria), execute, mark items complete.

**Why this priority**: Equally important as classification — this is what makes the system practical instead of bureaucratic.

**Independent Test**: Provide A-class and B-class tasks, verify correct artifacts (nothing for A, brief.md for B) without requiring full pipeline.

**Acceptance Scenarios**:

1. **Given** a class-A task, **When** process runs, **Then** no planning artifacts created, only post-completion verification prompted
2. **Given** a class-B task, **When** process runs, **Then** brief.md created with checklist items and done criteria
3. **Given** a completed brief, **When** all items checked, **Then** brief records completion status and timestamp

---

### User Story 3 - Full Spec-Driven Process for Complex Tasks (Priority: P2)

For Class C campaigns, the agent follows the full pipeline: specify requirements → plan approach → break into tasks → implement phase-by-phase. Each step produces a markdown artifact that gates the next. Artifacts are human-readable, git-tracked, and editable.

**Why this priority**: The heavyweight process that prevents architectural mistakes. Less frequent than A/B but critical when needed.

**Independent Test**: Provide a C-class task, verify the full artifact chain: spec.md → plan.md → tasks.md, each gating the next.

**Acceptance Scenarios**:

1. **Given** a class-C task, **When** specify runs, **Then** spec.md created with stories, requirements, success criteria
2. **Given** valid spec.md, **When** plan runs, **Then** plan.md created with approach, phases, risks
3. **Given** valid plan.md, **When** tasks runs, **Then** tasks.md created with phased, dependency-ordered list
4. **Given** no plan.md exists, **When** tasks is attempted, **Then** error returned requiring plan first

---

### User Story 4 - Mid-Process Escalation and Simplification (Priority: P2)

During execution, the agent discovers the task is more or less complex than classified. The system detects escalation signals (repeated failures, scope growth) or simplification signals (plan reveals triviality) and recommends reclassification.

**Why this priority**: Static classification is brittle. Adaptation prevents both over-engineering and under-engineering.

**Independent Test**: Simulate a B-class task that fails 3 times, verify escalation to C is recommended.

**Acceptance Scenarios**:

1. **Given** a B-class task with 3 consecutive failures, **When** system checks, **Then** escalation to C recommended
2. **Given** a C-class plan that reveals single-file change, **When** system checks, **Then** simplification to B recommended
3. **Given** accepted escalation, **Then** existing artifacts preserved and new process builds on them

---

### User Story 5 - Plan Outcome Memory (Priority: P3)

After completion, the system records: task description, weight class, outcome, surprises, duration. History is searchable via recall and informs future classifications.

**Why this priority**: Enhances classification accuracy over time but system works without it.

**Independent Test**: Complete a plan, verify outcome record created, search for it when classifying a similar future task.

**Acceptance Scenarios**:

1. **Given** completed campaign, **When** outcome recorded, **Then** markdown entry created with description, class, outcome, surprises, duration
2. **Given** new task similar to a past one, **When** classified, **Then** past outcome retrieved and influences classification

---

### User Story 6 - Parallel Implementation via Git Worktrees (Priority: P3)

For C-class tasks with independent subtasks, dispatch implementation to isolated git worktrees. Each worktree works on independent files, results merge back.

**Why this priority**: Optimization for speed, not a core requirement. System works without it.

**Independent Test**: Create a plan with two independent phases, dispatch each to a worktree, verify both complete and merge cleanly.

**Acceptance Scenarios**:

1. **Given** tasks.md with two independent phases, **When** parallel mode enabled, **Then** each runs in isolated worktree
2. **Given** non-conflicting worktree changes, **When** merge runs, **Then** both merged into main branch
3. **Given** conflicting changes, **When** merge runs, **Then** conflict reported for resolution

---

### Edge Cases

- Low classifier confidence (0.4): default to B, flag uncertainty
- A-class task fails verification: auto-escalate to B
- Requirements change mid-plan: allow incremental spec update, re-validate plan
- Outcome memory grows large: recall's decay handles relevance naturally
- Worktree creation fails: fall back to sequential, warn agent

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST classify tasks into weight classes A, B, C, D given description and optional context
- **FR-002**: System MUST return classification with confidence (0.0-1.0) and reasoning
- **FR-003**: System MUST enforce artifact prerequisites (plan requires spec, tasks require plan)
- **FR-004**: System MUST support Class A: no artifacts, verification prompt only
- **FR-005**: System MUST support Class B: brief.md with checklist and done criteria
- **FR-006**: System MUST support Class C: spec.md → plan.md → tasks.md → implement
- **FR-007**: System MUST detect escalation signals and recommend reclassification
- **FR-008**: System MUST record plan outcomes as searchable markdown entries
- **FR-009**: System MUST provide CLI interface (`deliberate classify`, `deliberate brief`, `deliberate spec`, etc.)
- **FR-010**: System MUST be importable as Python library for harness integration
- **FR-011**: Templates MUST be editable markdown files (self-modifiable by the agent)
- **FR-012**: System MUST support git worktree creation and merge for parallel implementation

### Key Entities

- **Task**: Unit of work with description, context, and weight class assignment
- **WeightClass**: Enum (A, B, C, D) with associated process and artifact requirements
- **Brief**: Lightweight planning artifact for Class B
- **Spec**: Requirements document for Class C/D
- **Plan**: Technical approach document for Class C/D
- **TaskList**: Phased, dependency-ordered implementation list for Class C/D
- **Outcome**: Record of completed plan results (for memory)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Classification completes in under 2 seconds (heuristic, no API call needed)
- **SC-002**: Class A tasks add zero overhead (no file creation, no planning)
- **SC-003**: Class B briefs produced in under 10 seconds
- **SC-004**: Classifier assigns correct weight class for 80% of tasks (against human judgment)
- **SC-005**: Agents using deliberate spend less time on mid-course corrections than without planning
- **SC-006**: System learnable from README and templates alone

## Assumptions

- Primary user is an autonomous AI agent in a heartbeat loop or interactive session
- Agent has access to git, Python, and standard CLI tools
- recall (hybrid search) is available for outcome memory
- Tasks arrive as natural language descriptions, sometimes with context (paths, errors)
- Agent harness manages the loop; deliberate manages planning within it
- Git worktrees are available (standard git feature)
- Templates are project-local (`.deliberate/templates/`), not global

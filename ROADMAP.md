# Roadmap

## Released

### v0.1.0 — Classify (MVP) ✅
- Heuristic task classifier (6 weighted signals)
- WeightClass enum (A/B/C/D) with Classification dataclass
- Artifact prerequisite enforcement
- Template loading with project-local overrides
- CLI: `deliberate classify`
- 44 tests

### v0.2.0 — Lightweight Process ✅
- Class A: verification-only flow
- Class B: brief.md generation with checklists
- Brief completion tracking
- CLI: `deliberate act`, `deliberate brief`

### v0.3.0 — Full Pipeline ✅
- Class C: spec → plan → tasks → implement with enforcement
- Campaign lifecycle management
- Template rendering for each step
- CLI: `deliberate spec`, `deliberate plan`, `deliberate tasks`

### v0.4.0 — Escalation ✅
- Mid-process reclassification detection
- Outcome-based stall signals
- Artifact preservation on escalation
- CLI: `deliberate check-status`

### v0.5.0 — Memory ✅
- Outcome recording after plan completion
- recall integration for past outcome search
- Classification improvement from experience
- CLI: `deliberate outcomes`

### v1.0.0 — Worktrees + Polish ✅
- Git worktree management for parallel implementation
- README, docs, and packaging complete
- 100 tests, all 6 user stories implemented
- Cross-model code review (Sonnet found and fixed 5 bugs)

## Aspirational (Post v1.0)

### Eval Framework
Build a benchmark for evaluating planning effectiveness:
- Curate a set of codebases + issues at varying complexity levels (trivial typos through architectural redesigns)
- Run agents with and without deliberate against the same issues
- Measure: classification accuracy, time to completion, mid-course corrections, final quality
- Compare weight-class routing effectiveness vs always-plan and never-plan baselines
- Publish results as a paper or blog post

### Multi-Agent Orchestration
- Dispatch sub-agents for research, review, and parallel implementation
- Define agent roles with read/write boundaries
- Merge agent work via git worktrees with conflict resolution
- Support agent teams where a planner delegates to implementers

### Cross-Model Review
- Built-in support for using different models at different stages
- /clarify and /analyze default to a different model than the primary
- Configurable model routing per step
- Cost tracking per model per step

### Self-Improving Templates
- Track template effectiveness (did plans from this template succeed?)
- Propose template modifications based on outcome patterns
- A/B test template variants on similar tasks
- Auto-evolve templates that work for your specific codebase

### Language/Framework Presets
- Preset template packs for common stacks (Python/FastAPI, Rust/CLI, TypeScript/React)
- Community-contributed presets
- Auto-detection from project files

### MCP Server
- Expose deliberate as an MCP server (like recall's)
- Tools: classify, brief, spec, plan, tasks, check-status
- Enables integration with any MCP-compatible agent

### Integration with Existing Tools
- Import from GitHub Issues (issue → classification → plan)
- Import from Linear/Jira tickets
- Export plans as GitHub project boards
- Sync with speckit artifacts bidirectionally

### Metrics Dashboard
- Visualization of classification accuracy over time
- Cost per plan (token usage tracking)
- Time to completion by weight class
- Escalation frequency analysis
- Pattern detection in failure modes

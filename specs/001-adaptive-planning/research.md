# Research: Adaptive Planning System

## Classification Approach Research

### Existing task complexity classifiers
- **speckit/autospec**: No classifier — assumes everything is a campaign. Task sizing guide says skip for <30min tasks.
- **Citadel /do router**: 6-dimension classifier (scope, complexity, intent, persistence, parallelism, taste) with regex → keyword → LLM cascade. Cheapest-first. Bias toward under-routing.
- **BMAD**: Scale-domain-adaptive intelligence. Planning depth auto-adjusts based on complexity detection.
- **My harness (ARCHITECTURE.md)**: Four levels (A/B/C/D) with heuristic signals. Outcome-based escalation.

### Key insight from Citadel
Classification should cascade from cheap to expensive: regex match → keyword detection → heuristic scoring → LLM (only if needed). First match wins. Most tasks are classifiable without an LLM.

### Heuristic accuracy estimates
Based on my experience from day one (79 commits, mix of trivial to complex):
- Word count + keywords correctly classify ~60% of tasks
- Adding file count estimate raises to ~75%
- Adding area familiarity (via recall) raises to ~85%
- LLM refinement for the remaining 15% is optional

## Template Design Research

### speckit template patterns (what to keep)
- Markdown with section headers as structure
- Given/When/Then acceptance scenarios
- Phased task lists with dependency markers
- Constitution gate checks

### speckit template problems (what to fix)
- 200-300 line prompt templates (too much context consumption)
- Schema duplicated in code AND templates
- No lightweight variant
- No incremental update support

### Design decision: templates should be SHORT
Each template should be under 50 lines. The template provides structure (sections, placeholders); the agent's system prompt provides the intelligence for filling them. Don't embed instructions in templates — that's what the agent's own knowledge is for.

## Escalation Signal Research

### From Citadel's circuit breaker
- 3 consecutive tool failures → inject "try different approach"
- 5 trips per session → hard stop "STOP. You are stuck."

### From my harness (outcome-based)
- No committed progress after 2 attempts → rethink
- Same failing test signature → reread requirements
- Reverted a decision → going in circles
- Scope grew significantly → re-plan

### Design decision: use outcome signals, not activity signals
"Editing same file 3 times" is a noisy proxy. "No progress after 2 attempts" measures actual stall. The escalation detector should check git history (committed progress) not tool call patterns (activity shape).

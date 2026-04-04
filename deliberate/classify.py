"""Weight class guide and escalation detection.

Provides a reference guide for choosing the right weight class,
replacing the heuristic classifier. The decision is best made by
the agent reading the guide, not by a numeric scoring model.
"""

from deliberate import WeightClass


GUIDE = """\
# Weight Class Guide

Pick the class that matches your task. When in doubt, start with B.

## Class A — Act
**Just do it.** No planning artifacts needed.
- Typo fixes, version bumps, config tweaks, renaming
- You know exactly what to change and where
- 1-2 files, fully reversible, takes under a minute
- If it fails on first attempt, escalate to B

## Class B — Brief
**Quick checklist, then do it.** Creates a brief.md with items to track.
- Bug fixes, small features, test additions, refactors
- Bounded scope: you can hold the whole task in your head
- 2-10 files, single session, mostly familiar territory
- Run: `deliberate brief "description"`

## Class C — Campaign
**Spec → Plan → Tasks → Implement.** Full pipeline with enforcement.
- Multi-file features, cross-module changes, API design
- Requires understanding code you haven't read yet
- 10+ files, multiple sessions, irreversible decisions (schema, API)
- Run: `deliberate campaign "name" "description"`

## Class D — Deliberate
**Research first, then campaign.** Adds research + spike before the pipeline.
- Unfamiliar codebase, unclear requirements, high stakes
- You need to learn before you can plan
- Architecture changes, new integrations, "I don't know where to start"
- Run: `deliberate campaign "name" "description"` (add research step)

## Escalation Rules
- A fails twice → escalate to B
- Scope grows during execution → bump up one class
- No progress after 3 attempts → bump up one class
- Fewer files than expected → consider simplifying down
- Check: `deliberate check-escalation <class> --attempts N`
"""


def get_guide() -> str:
    """Return the weight class reference guide."""
    return GUIDE


# --- Escalation Detection ---

CLASS_ORDER = [WeightClass.A, WeightClass.B, WeightClass.C, WeightClass.D]


def check_escalation(
    current_class: WeightClass,
    attempts: int = 1,
    scope_grew: bool = False,
    actual_files: int | None = None,
    failure_threshold: int = 3,
) -> dict | None:
    """Check if the current weight class should change.

    Returns None if no change recommended.
    Returns dict with 'recommendation' (WeightClass) and 'reason' (str) if change needed.
    """
    current_idx = CLASS_ORDER.index(current_class)

    # --- Escalation signals ---

    # Too many failed attempts → escalate
    if attempts >= failure_threshold:
        if current_idx < len(CLASS_ORDER) - 1:
            next_class = CLASS_ORDER[current_idx + 1]
            return {
                "recommendation": next_class,
                "reason": f"No progress after {attempts} attempts. Escalating from {current_class.value} to {next_class.value} for more structured planning.",
            }
        else:
            return {
                "recommendation": WeightClass.D,
                "reason": f"Already at maximum weight class (deliberate) after {attempts} attempts. You may be stuck — consider stepping back entirely, asking for help, or breaking the problem differently.",
            }

    # A-class tasks that fail once should escalate to B
    if current_class == WeightClass.A and attempts >= 2:
        return {
            "recommendation": WeightClass.B,
            "reason": f"A-class task needed {attempts} attempts. Escalating to brief for more structure.",
        }

    # Scope grew → escalate
    if scope_grew:
        if current_idx < len(CLASS_ORDER) - 1:
            next_class = CLASS_ORDER[current_idx + 1]
            return {
                "recommendation": next_class,
                "reason": f"Scope grew significantly during {current_class.value}. Escalating to {next_class.value}.",
            }

    # --- Simplification signals ---

    # Fewer files than expected → may be simpler
    if actual_files is not None:
        if actual_files <= 2 and current_class in (WeightClass.C, WeightClass.D):
            return {
                "recommendation": WeightClass.B if actual_files > 0 else WeightClass.A,
                "reason": f"Only {actual_files} file(s) affected — simpler than expected for {current_class.value}. Consider simplifying to {WeightClass.B.value}.",
            }
        elif actual_files <= 5 and current_class == WeightClass.C:
            return {
                "recommendation": WeightClass.B,
                "reason": f"Only {actual_files} files affected — this looks like a brief-level task, not a campaign.",
            }

    return None

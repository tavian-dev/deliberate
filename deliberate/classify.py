"""Task complexity classifier.

Uses weighted heuristic signals to classify tasks into weight classes
without requiring LLM calls. Classification takes <100ms.
"""

import re
from dataclasses import dataclass
from typing import Optional

from deliberate import Classification, WeightClass


# --- Signal Keywords ---

SIMPLICITY_KEYWORDS = frozenset([
    "fix", "typo", "rename", "update", "bump", "remove", "delete",
    "add comment", "format", "lint", "clean", "minor", "trivial",
    "tweak", "adjust", "correct", "small",
])

# Strong complexity signals (full weight)
COMPLEXITY_KEYWORDS_STRONG = frozenset([
    "redesign", "migrate", "architect", "overhaul", "rewrite",
    "infrastructure", "framework", "pipeline", "cross",
    "database schema", "api design",
])

# Weak complexity signals (half weight — common in tasks of all sizes)
COMPLEXITY_KEYWORDS_WEAK = frozenset([
    "implement", "build", "create", "integrate", "refactor",
    "design", "multi", "workflow", "authentication", "authorization",
])

IRREVERSIBILITY_KEYWORDS = frozenset([
    "schema", "migration", "api", "contract", "interface", "protocol",
    "public", "breaking", "deploy", "production", "release",
])

UNCERTAINTY_KEYWORDS = frozenset([
    "investigate", "explore", "research", "spike", "prototype",
    "evaluate", "compare", "decide", "unclear", "unknown",
    "might", "maybe", "possibly", "not sure",
])


# --- Signal Extractors ---

def _score_word_count(description: str) -> float:
    """Longer descriptions suggest more complex tasks. Returns 0.0-1.0."""
    words = len(description.split())
    if words < 10:
        return 0.0   # Very short → simple
    elif words < 30:
        return 0.25
    elif words < 60:
        return 0.5
    elif words < 120:
        return 0.75
    else:
        return 1.0   # Very long → complex


def _score_keywords(description: str) -> float:
    """Check for complexity/simplicity keywords. Returns -1.0 to 1.0.

    Uses word-boundary matching to avoid substring false positives
    (e.g., "fix" shouldn't match "prefix").
    """
    desc_lower = description.lower()
    # Extract individual words for boundary-safe single-keyword matching
    words = set(re.findall(r"\b[a-z]+\b", desc_lower))

    # Use word-boundary regex for multi-word keywords, set membership for single words
    def keyword_matches(keywords: frozenset) -> float:
        count = 0.0
        for kw in keywords:
            if " " in kw:
                if kw in desc_lower:
                    count += 1.0
            else:
                if kw in words:
                    count += 1.0
        return count

    simplicity = keyword_matches(SIMPLICITY_KEYWORDS)
    complexity_strong = keyword_matches(COMPLEXITY_KEYWORDS_STRONG)
    complexity_weak = keyword_matches(COMPLEXITY_KEYWORDS_WEAK) * 0.5  # Half weight for common verbs
    complexity = complexity_strong + complexity_weak

    total = simplicity + complexity
    if total == 0:
        return 0.0

    # Normalize: positive = complex, negative = simple
    score = (complexity - simplicity) / total
    return max(-1.0, min(1.0, score))


def _score_file_count(file_count: Optional[int]) -> float:
    """More files = more complex. Returns 0.0-1.0."""
    if file_count is None:
        return 0.5  # Unknown → neutral
    if file_count <= 2:
        return 0.0
    elif file_count <= 5:
        return 0.25
    elif file_count <= 10:
        return 0.5
    elif file_count <= 20:
        return 0.75
    else:
        return 1.0


def _score_reversibility(description: str) -> float:
    """Irreversible changes need more planning. Returns 0.0-1.0."""
    desc_lower = description.lower()
    hits = sum(1 for kw in IRREVERSIBILITY_KEYWORDS if kw in desc_lower)
    if hits == 0:
        return 0.0
    elif hits <= 2:
        return 0.5
    else:
        return 1.0


def _score_familiarity(familiarity: Optional[float]) -> float:
    """Unfamiliar areas need more planning. Returns 0.0-1.0 (inverted)."""
    if familiarity is None:
        return 0.5  # Unknown → neutral
    return 1.0 - familiarity  # High familiarity → low complexity signal


# --- Main Classifier ---

# Signal weights (must sum to 1.0)
WEIGHTS = {
    "word_count": 0.15,
    "keywords": 0.25,
    "file_count": 0.20,
    "reversibility": 0.15,
    "familiarity": 0.15,
    "uncertainty": 0.10,
}


def _has_uncertainty(description: str) -> float:
    """Check for uncertainty/exploration language. Returns 0.0-1.0."""
    desc_lower = description.lower()
    hits = sum(1 for kw in UNCERTAINTY_KEYWORDS if kw in desc_lower)
    return min(1.0, hits * 0.4)


def classify(
    description: str,
    context: Optional[dict] = None,
) -> Classification:
    """Classify a task's complexity into a weight class.

    Args:
        description: Natural language task description
        context: Optional dict with keys:
            - file_count: estimated number of files affected
            - familiarity: 0.0-1.0 how familiar with this area
            - past_outcomes: list of relevant past outcome dicts

    Returns:
        Classification with weight_class, confidence, reasoning, signals
    """
    ctx = context or {}

    # Extract signals
    signals = {
        "word_count": _score_word_count(description),
        "keywords": (_score_keywords(description) + 1) / 2,  # Normalize to 0-1
        "file_count": _score_file_count(ctx.get("file_count")),
        "reversibility": _score_reversibility(description),
        "familiarity": _score_familiarity(ctx.get("familiarity")),
        "uncertainty": _has_uncertainty(description),
    }

    # Weighted composite score (0.0 = trivial, 1.0 = highly complex)
    composite = sum(signals[k] * WEIGHTS[k] for k in WEIGHTS)

    # Map composite to weight class
    if composite < 0.20:
        weight_class = WeightClass.A
    elif composite < 0.45:
        weight_class = WeightClass.B
    elif composite < 0.70:
        weight_class = WeightClass.C
    else:
        weight_class = WeightClass.D

    # Confidence: higher when signals agree, lower when mixed
    signal_values = list(signals.values())
    variance = sum((s - composite) ** 2 for s in signal_values) / len(signal_values)
    confidence = max(0.3, min(1.0, 1.0 - variance * 2))

    # Adjust for past outcomes if available
    past = ctx.get("past_outcomes", [])
    if past:
        # If past similar tasks needed higher class, boost confidence in that direction
        past_classes = [o.get("weight_class") for o in past if o.get("weight_class")]
        if past_classes:
            reasoning_addendum = f" Past similar tasks used class(es): {', '.join(past_classes)}."
        else:
            reasoning_addendum = ""
    else:
        reasoning_addendum = ""

    # Generate reasoning
    dominant_signal = max(signals, key=lambda k: abs(signals[k] - 0.5))
    reasoning = (
        f"Classified as {weight_class.value} (confidence: {confidence:.2f}). "
        f"Composite score: {composite:.2f}. "
        f"Dominant signal: {dominant_signal} ({signals[dominant_signal]:.2f})."
        f"{reasoning_addendum}"
    )

    return Classification(
        task_description=description,
        weight_class=weight_class,
        confidence=round(confidence, 2),
        reasoning=reasoning,
        signals=signals,
        context=ctx,
    )


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

"""Tests for task classification."""

import pytest
from deliberate import WeightClass, Classification
from deliberate.classify import (
    classify, _score_word_count, _score_keywords,
    _score_file_count, _score_reversibility, _score_familiarity,
)


# --- Signal extractor tests ---

class TestScoreWordCount:
    def test_very_short(self):
        assert _score_word_count("fix typo") == 0.0

    def test_short(self):
        assert _score_word_count("add input validation to the login form and check error messages for each field") == 0.25

    def test_medium(self):
        desc = " ".join(["word"] * 45)
        assert _score_word_count(desc) == 0.5

    def test_long(self):
        desc = " ".join(["word"] * 80)
        assert _score_word_count(desc) == 0.75

    def test_very_long(self):
        desc = " ".join(["word"] * 150)
        assert _score_word_count(desc) == 1.0


class TestScoreKeywords:
    def test_simplicity_keywords(self):
        score = _score_keywords("fix a typo in the readme")
        assert score < 0  # Negative = simple

    def test_complexity_keywords(self):
        score = _score_keywords("redesign the authentication infrastructure and integrate new framework")
        assert score > 0  # Positive = complex

    def test_neutral(self):
        score = _score_keywords("do something with the thing")
        assert -0.3 < score < 0.3  # Near zero

    def test_uncertainty_not_in_keywords(self):
        # Uncertainty is handled by _has_uncertainty, not _score_keywords
        score = _score_keywords("investigate whether we should evaluate options")
        assert score == 0.0  # No complexity/simplicity keywords

    def test_no_substring_false_positives(self):
        # "fix" shouldn't match "prefix", "api" shouldn't match "capital"
        score = _score_keywords("the prefix of the capital city")
        assert score == 0.0  # No actual keywords present


class TestScoreFileCount:
    def test_none(self):
        assert _score_file_count(None) == 0.5  # Unknown = neutral

    def test_few(self):
        assert _score_file_count(1) == 0.0
        assert _score_file_count(2) == 0.0

    def test_moderate(self):
        assert _score_file_count(5) == 0.25
        assert _score_file_count(8) == 0.5

    def test_many(self):
        assert _score_file_count(15) == 0.75
        assert _score_file_count(30) == 1.0


class TestScoreReversibility:
    def test_reversible(self):
        assert _score_reversibility("fix typo in readme") == 0.0

    def test_somewhat_irreversible(self):
        score = _score_reversibility("update the API contract")
        assert score > 0

    def test_very_irreversible(self):
        score = _score_reversibility("change database schema and public API for production deploy")
        assert score > 0.5


class TestScoreFamiliarity:
    def test_none(self):
        assert _score_familiarity(None) == 0.5  # Unknown = neutral

    def test_very_familiar(self):
        assert _score_familiarity(1.0) == 0.0  # Familiar = low complexity

    def test_unfamiliar(self):
        assert _score_familiarity(0.0) == 1.0  # Unfamiliar = high complexity


# --- Main classifier tests ---

class TestClassify:
    def test_trivial_task_class_a(self):
        result = classify("fix typo in README")
        assert result.weight_class == WeightClass.A
        assert result.confidence > 0.5

    def test_small_task_class_b(self):
        result = classify("add input validation to the login form fields")
        assert result.weight_class in (WeightClass.A, WeightClass.B)

    def test_complex_task_class_c(self):
        result = classify(
            "redesign the authentication system to support OAuth2 and SAML, "
            "including database schema migration, API contract updates, "
            "and integration with the existing user management infrastructure"
        )
        assert result.weight_class in (WeightClass.C, WeightClass.D)

    def test_uncertain_task_class_d(self):
        result = classify(
            "investigate whether we should migrate from PostgreSQL to a "
            "distributed database, evaluate options, prototype the riskiest "
            "parts, and decide on an approach. Unclear requirements."
        )
        assert result.weight_class in (WeightClass.C, WeightClass.D)

    def test_ambiguous_defaults_to_b(self):
        result = classify("update the thing")
        assert result.weight_class in (WeightClass.A, WeightClass.B)

    def test_context_shifts_classification(self):
        # Same task, but with many files → higher class
        base = classify("add logging throughout the application")
        with_files = classify("add logging throughout the application",
                             context={"file_count": 25})
        assert with_files.weight_class.value >= base.weight_class.value

    def test_familiarity_context(self):
        # Unfamiliar area → higher class
        unfamiliar = classify("update the auth module",
                             context={"familiarity": 0.0})
        familiar = classify("update the auth module",
                           context={"familiarity": 1.0})
        # Unfamiliar should be same or higher class
        class_order = [WeightClass.A, WeightClass.B, WeightClass.C, WeightClass.D]
        assert class_order.index(unfamiliar.weight_class) >= class_order.index(familiar.weight_class)

    def test_returns_classification_object(self):
        result = classify("any task")
        assert isinstance(result, Classification)
        assert isinstance(result.weight_class, WeightClass)
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.reasoning) > 0
        assert len(result.signals) > 0

    def test_confidence_range(self):
        result = classify("a task")
        assert 0.3 <= result.confidence <= 1.0

    def test_signals_populated(self):
        result = classify("redesign something complex")
        assert "word_count" in result.signals
        assert "keywords" in result.signals
        assert "file_count" in result.signals
        assert "reversibility" in result.signals
        assert "familiarity" in result.signals

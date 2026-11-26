import pytest

from agentic_bioinformatics_research.metrics.canaries import canary_recall


def test_canary_recall_per_class():
    result = canary_recall({"CWE-79": 10, "CWE-78": 5}, {"CWE-79": 8, "CWE-78": 1})
    assert result == {"CWE-79": 0.8, "CWE-78": 0.2}


def test_canary_recall_rejects_more_caught_than_injected():
    with pytest.raises(ValueError):
        canary_recall({"A": 1}, {"A": 3})


def test_canary_recall_rejects_negative_counts():
    with pytest.raises(ValueError):
        canary_recall({"A": -1}, {"A": 0})


def test_canary_recall_skips_classes_without_canaries():
    assert canary_recall({"A": 0}, {"A": 0}) == {}

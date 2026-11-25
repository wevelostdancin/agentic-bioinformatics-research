from agentic_bioinformatics_research.metrics.canaries import canary_recall


def test_canary_recall_per_class():
    result = canary_recall({"CWE-79": 10, "CWE-78": 5}, {"CWE-79": 8, "CWE-78": 1})
    assert result == {"CWE-79": 0.8, "CWE-78": 0.2}

import pytest

from agentic_bioinformatics_research.harness import (
    ORCHESTRATION_PROTOCOLS,
    BudgetExceededError,
    HarnessAdapter,
    enforce_budget,
)


def test_dummy_adapter_satisfies_protocol():
    class Dummy:
        def run(self, config: dict) -> dict:
            return config

    assert isinstance(Dummy(), HarnessAdapter)


def test_orchestration_protocols_are_listed():
    assert ORCHESTRATION_PROTOCOLS == (
        "single",
        "parallel_vote",
        "parallel_judge",
        "debate",
        "supervisor",
        "blackboard",
    )


def test_enforce_budget_allows_within_budget():
    enforce_budget({"in_tokens": 10, "out_tokens": 5}, 100)


def test_enforce_budget_raises_over_budget():
    with pytest.raises(BudgetExceededError):
        enforce_budget({"in_tokens": 90, "out_tokens": 20}, 100)


def test_enforce_budget_rejects_non_positive_budget():
    with pytest.raises(ValueError):
        enforce_budget({"in_tokens": 0, "out_tokens": 0}, 0)

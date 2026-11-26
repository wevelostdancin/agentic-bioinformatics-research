from typing import Protocol, runtime_checkable

# Fixed vocabulary for the main experimental factor: how the swarm is organised.
ORCHESTRATION_PROTOCOLS: tuple[str, ...] = (
    "single",
    "parallel_vote",
    "parallel_judge",
    "debate",
    "supervisor",
    "blackboard",
)


class BudgetExceededError(RuntimeError):
    pass


def enforce_budget(tokens_used: dict, budget_tokens: int) -> None:
    if budget_tokens <= 0:
        raise ValueError("budget_tokens must be positive")
    spent = int(tokens_used.get("in_tokens", 0)) + int(tokens_used.get("out_tokens", 0))
    if spent > budget_tokens:
        raise BudgetExceededError(f"spent {spent} tokens of a {budget_tokens} budget")


@runtime_checkable
class HarnessAdapter(Protocol):
    def run(self, config: dict) -> dict: ...

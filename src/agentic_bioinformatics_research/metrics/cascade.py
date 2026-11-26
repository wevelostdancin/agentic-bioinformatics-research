def cascade_depth(events: list[dict]) -> int:
    """Longest chain of artifact references in a trace, counted in edges."""
    children: dict[str, set[str]] = {}
    nodes: set[str] = set()
    for event in events:
        artifact = event.get("artifact_id")
        if not artifact:
            continue
        nodes.add(artifact)
        for reference in event.get("references") or ():
            nodes.add(reference)
            children.setdefault(reference, set()).add(artifact)

    memo: dict[str, int] = {}

    def depth(node: str, stack: set[str]) -> int:
        if node in memo:
            return memo[node]
        if node in stack:
            raise ValueError("cycle in artifact references")
        stack.add(node)
        longest = 0
        for child in children.get(node, ()):
            longest = max(longest, 1 + depth(child, stack))
        stack.discard(node)
        memo[node] = longest
        return longest

    return max((depth(node, set()) for node in sorted(nodes)), default=0)


def decoy_uptake(events: list[dict], decoy_ids: set[str]) -> int:
    """How many distinct agents referenced at least one decoy artifact."""
    agents = set()
    for event in events:
        agent = event.get("agent_id")
        if agent and set(event.get("references") or ()) & decoy_ids:
            agents.add(agent)
    return len(agents)


def silent_corruption_rate(confirmed: int, correct: int) -> float | None:
    """Share of confirmed findings that are wrong; None when nothing was confirmed."""
    if confirmed < 0 or correct < 0 or correct > confirmed:
        raise ValueError("invalid confirmed/correct counts")
    if confirmed == 0:
        return None
    return (confirmed - correct) / confirmed


def robustness_drop(clean: float, perturbed: float) -> float | None:
    """Relative loss from the clean condition; None when the baseline is zero."""
    if clean == 0:
        return None
    return (clean - perturbed) / clean

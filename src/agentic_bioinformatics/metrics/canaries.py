def canary_recall(injected: dict[str, int], caught: dict[str, int]) -> dict[str, float]:
    return {
        cwe: caught.get(cwe, 0) / total
        for cwe, total in injected.items()
        if total > 0
    }

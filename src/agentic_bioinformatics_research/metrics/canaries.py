def canary_recall(injected: dict[str, int], caught: dict[str, int]) -> dict[str, float]:
    """Per-class recall over injected canaries.

    Raises ValueError on impossible counts: recall above 1.0 means double
    counting or false attribution and would silently corrupt a results table.
    """
    result: dict[str, float] = {}
    for cwe, total in injected.items():
        hits = caught.get(cwe, 0)
        if total < 0 or hits < 0:
            raise ValueError("canary counts must be non-negative")
        if total == 0:
            continue
        if hits > total:
            raise ValueError(
                f"caught {hits} of {total} {cwe} canaries: "
                "double counting or false attribution"
            )
        result[cwe] = hits / total
    return result

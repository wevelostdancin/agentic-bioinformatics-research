def cohen_kappa(a: list[int], b: list[int]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("two non-empty, equal-length verdict lists are required")
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    categories = set(a) | set(b)
    expected = sum((a.count(c) / n) * (b.count(c) / n) for c in categories)
    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1.0 - expected)


def position_swap_agreement(a: list[int], b: list[int]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("two non-empty, equal-length verdict lists are required")
    return sum(x == y for x, y in zip(a, b)) / len(a)

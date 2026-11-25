import math


def _validate(n1: int, n2: int, m: int) -> None:
    if n1 < 0 or n2 < 0 or m < 0 or m > min(n1, n2):
        raise ValueError("invalid capture-recapture inputs")


def capture_recapture(n1: int, n2: int, m: int) -> float:
    _validate(n1, n2, m)
    if m == 0:
        return float("inf")
    return (n1 + 1) * (n2 + 1) / (m + 1) - 1


def capture_recapture_ci(n1: int, n2: int, m: int) -> tuple[float, float]:
    _validate(n1, n2, m)
    observed = n1 + n2 - m
    if m == 0:
        return float(observed), float("inf")
    estimate = capture_recapture(n1, n2, m)
    variance = (
        (n1 + 1) * (n2 + 1) * (n1 - m) * (n2 - m) / ((m + 1) ** 2 * (m + 2))
    )
    margin = 1.96 * math.sqrt(variance)
    lower = max(observed, estimate - margin)
    upper = estimate + margin
    if upper <= lower:
        upper = lower + 1.0
    return lower, upper


def saturation_curve(counts: list[int]) -> list[float]:
    total = sum(counts)
    if total == 0:
        return []
    cumulative = 0
    result = []
    for count in counts:
        cumulative += count
        result.append(cumulative / total)
    return result


def coverage_matrix(
    cells: list[tuple[str, str]], covered: set[tuple[str, str]]
) -> dict:
    found = set(covered)
    uncovered = [cell for cell in cells if cell not in found]
    return {
        "total": len(cells),
        "covered": len(cells) - len(uncovered),
        "uncovered": len(uncovered),
        "uncovered_cells": uncovered,
    }

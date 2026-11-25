def capture_recapture(n1: int, n2: int, m: int) -> float:
    if m == 0:
        return 0.0
    return n1 * n2 / m


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

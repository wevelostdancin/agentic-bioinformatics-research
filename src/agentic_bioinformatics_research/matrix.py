import itertools


def expand_matrix(factors: dict[str, list], fixed: dict | None = None) -> list[dict]:
    """Expand a factor grid into one config dict per experimental cell.

    Factor names are sorted, so the cell order does not depend on the order the
    keys happen to have in YAML.
    """
    names = sorted(factors)
    for name in names:
        if not factors[name]:
            raise ValueError(f"factor {name!r} has no values")
    cells = []
    for combo in itertools.product(*(factors[name] for name in names)):
        cell = dict(fixed or {})
        cell.update(dict(zip(names, combo, strict=True)))
        cells.append(cell)
    return cells

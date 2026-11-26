import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, stdev

import yaml

# Two-sided 95% Student-t critical values for df = 1..30. Above 30 the normal
# approximation (1.96) is within 5% and is used instead.
_T95: dict[int, float] = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    21: 2.080,
    22: 2.074,
    23: 2.069,
    24: 2.064,
    25: 2.060,
    26: 2.056,
    27: 2.052,
    28: 2.048,
    29: 2.045,
    30: 2.042,
}


def set_seed(seed: int) -> None:
    random.seed(seed)


def critical_t(n: int) -> float:
    """Two-sided 95% critical value for a sample of n observations."""
    if n < 2:
        raise ValueError("at least two observations are required")
    return _T95.get(n - 1, 1.96)


def aggregate(values: list[float]) -> dict:
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": None, "std": None, "ci_low": None, "ci_high": None}
    mean = fmean(values)
    sd = stdev(values) if n > 1 else None
    ci_low = ci_high = None
    if sd is not None:
        margin = critical_t(n) * sd / math.sqrt(n)
        ci_low, ci_high = mean - margin, mean + margin
    return {"n": n, "mean": mean, "std": sd, "ci_low": ci_low, "ci_high": ci_high}


def _run_config(run_dir: Path) -> dict:
    config_path = run_dir / "config.yaml"
    if not config_path.is_file():
        return {}
    return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def aggregate_runs(
    base: Path,
    exp: str,
    git_sha: str | None = None,
    metric: str = "findings",
    group_by: tuple[str, ...] = (),
) -> dict:
    """Aggregate one numeric metric over runs, optionally grouped by config factors.

    Without group_by the flat aggregate is returned; with it, a mapping from the
    factor values (joined by a pipe) to that group's aggregate.
    """
    groups: dict[str, list[float]] = {}
    for path in sorted((base / exp / "runs").glob("*/metrics.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        value = data.get(metric)
        if not _is_number(value):
            continue
        cfg = _run_config(path.parent)
        if git_sha is not None and cfg.get("git_sha") != git_sha:
            continue
        key = "|".join(str(cfg.get(name)) for name in group_by)
        groups.setdefault(key, []).append(float(value))
    if not group_by:
        return aggregate(groups.get("", []))
    return {key: aggregate(values) for key, values in sorted(groups.items())}


@dataclass
class TokenCounter:
    in_tokens: int = 0
    out_tokens: int = 0

    def add(self, in_tokens: int, out_tokens: int) -> None:
        self.in_tokens += in_tokens
        self.out_tokens += out_tokens

    def as_dict(self) -> dict:
        return {"in_tokens": self.in_tokens, "out_tokens": self.out_tokens}

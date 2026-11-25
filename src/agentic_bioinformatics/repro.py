import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, stdev

import yaml


def set_seed(seed: int) -> None:
    random.seed(seed)


def aggregate(values: list[float]) -> dict:
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": None, "std": None, "ci_low": None, "ci_high": None}
    mean = fmean(values)
    sd = stdev(values) if n > 1 else None
    ci_low = ci_high = None
    if sd is not None:
        margin = 1.96 * sd / math.sqrt(n)
        ci_low, ci_high = mean - margin, mean + margin
    return {"n": n, "mean": mean, "std": sd, "ci_low": ci_low, "ci_high": ci_high}


def aggregate_runs(base: Path, exp: str, git_sha: str | None = None) -> dict:
    values = []
    for path in sorted((base / exp / "runs").glob("*/metrics.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "findings" not in data:
            continue
        if git_sha is not None:
            config_path = path.parent / "config.yaml"
            if not config_path.is_file():
                continue
            cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            if cfg.get("git_sha") != git_sha:
                continue
        values.append(data["findings"])
    return aggregate(values)


@dataclass
class TokenCounter:
    in_tokens: int = 0
    out_tokens: int = 0

    def add(self, in_tokens: int, out_tokens: int) -> None:
        self.in_tokens += in_tokens
        self.out_tokens += out_tokens

    def as_dict(self) -> dict:
        return {"in_tokens": self.in_tokens, "out_tokens": self.out_tokens}

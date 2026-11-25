import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

EVIDENCE_CLASSES: tuple[str, ...] = (
    "hypothesis",
    "code_reference",
    "static_analyzer",
    "reproducible_poc",
    "sanitizer_crash",
)
_CONFIRMED_CLASSES = {"reproducible_poc", "sanitizer_crash"}


def new_run(exp: str, seed: int, base: Path = Path("experiments")) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = base / exp / "runs" / f"{stamp}-{seed}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_config(run_dir: Path, config: dict) -> None:
    text = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
    (run_dir / "config.yaml").write_text(text, encoding="utf-8")


def append_trace(run_dir: Path, event: dict) -> None:
    line = json.dumps(event, ensure_ascii=False) + "\n"
    with (run_dir / "trace.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(line)


def write_metrics(run_dir: Path, metrics: dict) -> None:
    text = json.dumps(metrics, ensure_ascii=False, indent=2) + "\n"
    (run_dir / "metrics.json").write_text(text, encoding="utf-8")


def require_confirmed(evidence: str) -> None:
    if evidence not in _CONFIRMED_CLASSES:
        raise ValueError(f"{evidence!r} is not an executable proof")

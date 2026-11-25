import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

# Единственный источник правды: класс -> является ли исполняемым доказательством.
_EVIDENCE: dict[str, bool] = {
    "hypothesis": False,
    "code_reference": False,
    "static_analyzer": False,
    "reproducible_test": True,
    "reproducible_poc": True,
    "sanitizer_crash": True,
    "ground_truth": True,
}
EVIDENCE_CLASSES: tuple[str, ...] = tuple(_EVIDENCE)


def new_run(exp: str, seed: int, base: Path = Path("experiments")) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = base / exp / "runs" / f"{stamp}-{seed}"
    run_dir.mkdir(parents=True, exist_ok=False)
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


def write_summary(run_dir: Path, text: str) -> None:
    (run_dir / "summary.md").write_text(text.rstrip() + "\n", encoding="utf-8")


def require_confirmed(evidence: str, artifact: Path | None = None) -> None:
    if not _EVIDENCE.get(evidence, False):
        raise ValueError(f"{evidence!r} is not an executable proof")
    if artifact is not None and not artifact.is_file():
        raise FileNotFoundError(f"evidence artifact not found: {artifact}")

import hashlib
import json
import re
import subprocess
from pathlib import Path

import yaml

from agentic_bioinformatics_research.harness import ORCHESTRATION_PROTOCOLS

ARTIFACTS = ("config.yaml", "trace.jsonl", "metrics.json", "summary.md")
REQUIRED_CONFIG_FIELDS = (
    "model_version",
    "harness_version",
    "seed",
    "git_sha",
    "uv_lock_sha256",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def snapshot(repo_root: Path, config: dict) -> dict:
    head = _git(repo_root, "rev-parse", "HEAD")
    git_sha = head.strip() if head and head.strip() else "unknown"
    status = _git(repo_root, "status", "--porcelain")
    lock = repo_root / "uv.lock"
    data_root = repo_root / "data"
    data_hashes = {}
    if data_root.is_dir():
        for path in sorted(data_root.rglob("*")):
            if path.is_file() and path.name != ".gitkeep":
                data_hashes[str(path.relative_to(repo_root))] = _sha256(path)
    return {
        "git_sha": git_sha,
        "git_dirty": bool(status.strip()) if status is not None else None,
        "uv_lock_sha256": _sha256(lock) if lock.is_file() else "unknown",
        "data_sha256": data_hashes,
        "prompt_version": config.get("prompt_version", "unknown"),
        "tool_versions": config.get("tool_versions", {}),
    }


def validate_run(run_dir: Path, *, require_clean: bool = False) -> list[str]:
    issues = []
    for name in ARTIFACTS:
        if not (run_dir / name).is_file():
            issues.append(f"missing {name}")
    cfg = {}
    config_path = run_dir / "config.yaml"
    if config_path.is_file():
        try:
            cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            issues.append("invalid config.yaml")
    for key in REQUIRED_CONFIG_FIELDS:
        if key not in cfg:
            issues.append(f"missing config field: {key}")
    for key, length in (("git_sha", 40), ("uv_lock_sha256", 64)):
        value = cfg.get(key)
        if value is not None and (
            not isinstance(value, str)
            or not re.fullmatch(rf"[0-9a-f]{{{length}}}", value)
        ):
            issues.append(f"invalid {key}")
    protocol = cfg.get("orchestration_protocol")
    if protocol is not None and protocol not in ORCHESTRATION_PROTOCOLS:
        issues.append(f"unknown orchestration_protocol: {protocol!r}")
    if require_clean and cfg.get("git_dirty"):
        issues.append("run recorded from a dirty working tree")
    trace_text = ""
    trace_path = run_dir / "trace.jsonl"
    if trace_path.is_file():
        trace_text = trace_path.read_text(encoding="utf-8").strip()
    if not trace_text:
        issues.append("empty trace.jsonl")
    else:
        for line in trace_text.splitlines():
            try:
                json.loads(line)
            except json.JSONDecodeError:
                issues.append("invalid trace.jsonl line")
                break
    metrics = {}
    metrics_path = run_dir / "metrics.json"
    if metrics_path.is_file():
        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            issues.append("invalid metrics.json")
            metrics = {}
        for key in ("findings", "confirmed_count", "evidence_class", "tokens_used"):
            if key not in metrics:
                issues.append(f"missing metrics field: {key}")
    budget = cfg.get("budget_tokens")
    tokens = metrics.get("tokens_used")
    if (
        isinstance(budget, int)
        and not isinstance(budget, bool)
        and isinstance(tokens, dict)
    ):
        spent = int(tokens.get("in_tokens", 0)) + int(tokens.get("out_tokens", 0))
        if spent > budget:
            issues.append(f"tokens_used {spent} exceeds budget_tokens {budget}")
    return issues


def require_valid_run(run_dir: Path, *, require_clean: bool = False) -> None:
    issues = validate_run(run_dir, require_clean=require_clean)
    if issues:
        raise ValueError("; ".join(issues))

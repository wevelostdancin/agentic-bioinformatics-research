import hashlib
import subprocess
from pathlib import Path

import yaml

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


def snapshot(repo_root: Path, config: dict) -> dict:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    git_sha = (
        result.stdout.strip()
        if result.returncode == 0 and result.stdout.strip()
        else "unknown"
    )
    lock = repo_root / "uv.lock"
    data_root = repo_root / "data"
    data_hashes = {}
    if data_root.is_dir():
        for path in sorted(data_root.rglob("*")):
            if path.is_file() and path.name != ".gitkeep":
                data_hashes[str(path.relative_to(repo_root))] = _sha256(path)
    return {
        "git_sha": git_sha,
        "uv_lock_sha256": _sha256(lock) if lock.is_file() else "unknown",
        "data_sha256": data_hashes,
        "prompt_version": config.get("prompt_version", "unknown"),
        "tool_versions": config.get("tool_versions", {}),
    }


def validate_run(run_dir: Path) -> list[str]:
    issues = []
    for name in ARTIFACTS:
        if not (run_dir / name).is_file():
            issues.append(f"missing {name}")
    config_path = run_dir / "config.yaml"
    if config_path.is_file():
        cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        for key in REQUIRED_CONFIG_FIELDS:
            if key not in cfg:
                issues.append(f"missing config field: {key}")
    return issues


def require_valid_run(run_dir: Path) -> None:
    issues = validate_run(run_dir)
    if issues:
        raise ValueError("; ".join(issues))

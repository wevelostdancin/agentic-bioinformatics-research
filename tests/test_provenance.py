import json
from pathlib import Path

import pytest
import yaml

from agentic_bioinformatics.provenance import require_valid_run, snapshot, validate_run


def _complete_run(tmp_path, *, git_sha="a" * 40, lock_sha="b" * 64, trace=None, metrics=None):
    cfg = {
        "model_version": "v1",
        "harness_version": "v1",
        "seed": 1,
        "git_sha": git_sha,
        "uv_lock_sha256": lock_sha,
    }
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    (tmp_path / "trace.jsonl").write_text(
        trace if trace is not None else '{"event": "start"}\n', encoding="utf-8"
    )
    full_metrics = {
        "findings": 0,
        "confirmed_count": 0,
        "evidence_class": "hypothesis",
        "tokens_used": {"in_tokens": 0, "out_tokens": 0},
    }
    if metrics is not None:
        full_metrics.update(metrics)
    (tmp_path / "metrics.json").write_text(
        json.dumps(full_metrics), encoding="utf-8"
    )
    (tmp_path / "summary.md").write_text("x", encoding="utf-8")


def test_snapshot_contains_required_keys():
    root = Path(__file__).resolve().parents[1]
    s = snapshot(root, {"prompt_version": "v1"})
    assert set(s) >= {"git_sha", "uv_lock_sha256", "data_sha256", "prompt_version"}
    assert len(s["git_sha"]) == 40 and len(s["uv_lock_sha256"]) == 64


def test_snapshot_hashes_data_files(tmp_path):
    (tmp_path / "data/raw").mkdir(parents=True)
    (tmp_path / "data/raw/a.txt").write_text("x")
    s = snapshot(tmp_path, {})
    assert "data/raw/a.txt" in s["data_sha256"]


def test_validate_run_reports_missing_artifacts(tmp_path):
    issues = validate_run(tmp_path)
    assert any("config.yaml" in i for i in issues)


def test_validate_run_accepts_complete_run(tmp_path):
    _complete_run(tmp_path)
    assert validate_run(tmp_path) == []


def test_validate_run_rejects_unknown_hashes(tmp_path):
    _complete_run(tmp_path, git_sha="unknown", lock_sha="unknown")
    issues = validate_run(tmp_path)
    assert any("git_sha" in i for i in issues)
    assert any("uv_lock_sha256" in i for i in issues)


def test_validate_run_rejects_empty_trace(tmp_path):
    _complete_run(tmp_path, trace="")
    assert any("trace.jsonl" in i for i in validate_run(tmp_path))


def test_validate_run_rejects_missing_metric_fields(tmp_path):
    _complete_run(tmp_path)
    (tmp_path / "metrics.json").write_text("{}", encoding="utf-8")
    assert any("missing metrics field" in i for i in validate_run(tmp_path))


def test_validate_run_handles_broken_yaml(tmp_path):
    (tmp_path / "config.yaml").write_text("a: [unclosed", encoding="utf-8")
    for name in ("trace.jsonl", "metrics.json", "summary.md"):
        (tmp_path / name).write_text("x", encoding="utf-8")
    assert any("config.yaml" in i for i in validate_run(tmp_path))


def test_require_valid_run_raises(tmp_path):
    with pytest.raises(ValueError):
        require_valid_run(tmp_path)

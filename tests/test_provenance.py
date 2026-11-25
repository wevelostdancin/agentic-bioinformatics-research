from pathlib import Path

import yaml

from agentic_bioinformatics.provenance import snapshot, validate_run


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
    cfg = {
        "model_version": "v1",
        "harness_version": "v1",
        "seed": 1,
        "git_sha": "0" * 40,
        "uv_lock_sha256": "0" * 64,
    }
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    (tmp_path / "trace.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "metrics.json").write_text("{}", encoding="utf-8")
    (tmp_path / "summary.md").write_text("x", encoding="utf-8")
    assert validate_run(tmp_path) == []

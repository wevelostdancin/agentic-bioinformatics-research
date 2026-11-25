import pytest

from agentic_bioinformatics.run import (
    append_trace,
    new_run,
    require_confirmed,
    write_config,
    write_metrics,
    write_summary,
)


def test_new_run_creates_timestamp_seed_dir(tmp_path):
    d = new_run("debate_vs_sampling", 42, base=tmp_path)
    assert d.exists() and "42" in d.name


def test_run_artifacts(tmp_path):
    d = new_run("e", 1, base=tmp_path)
    write_config(d, {"model": "deepseek"})
    append_trace(d, {"event": "start"})
    write_metrics(d, {"precision": 0.8})
    assert (d / "config.yaml").exists()
    assert (d / "trace.jsonl").read_text().count("\n") == 1
    assert (d / "metrics.json").exists()


def test_confirmed_requires_proof():
    with pytest.raises(ValueError):
        require_confirmed("hypothesis")
    require_confirmed("reproducible_poc")


def test_new_run_paths_are_unique(tmp_path):
    first = new_run("e", 1, base=tmp_path)
    second = new_run("e", 1, base=tmp_path)
    assert first != second


def test_new_run_refuses_existing_dir(tmp_path, monkeypatch):
    from datetime import datetime

    import agentic_bioinformatics.run as run_mod

    class Frozen:
        @staticmethod
        def now(tz):
            return datetime(2026, 1, 1, tzinfo=tz)

    monkeypatch.setattr(run_mod, "datetime", Frozen)
    new_run("e", 1, base=tmp_path)
    with pytest.raises(FileExistsError):
        new_run("e", 1, base=tmp_path)


def test_confirmed_accepts_test_and_ground_truth():
    require_confirmed("reproducible_test")
    require_confirmed("ground_truth")


def test_confirmed_rejects_missing_artifact(tmp_path):
    with pytest.raises(FileNotFoundError):
        require_confirmed("reproducible_poc", artifact=tmp_path / "missing.py")


def test_write_summary(tmp_path):
    d = new_run("e", 1, base=tmp_path)
    write_summary(d, "Итог: findings=0")
    assert (d / "summary.md").read_text(encoding="utf-8") == "Итог: findings=0\n"

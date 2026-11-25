import pytest

from agentic_bioinformatics.run import (
    append_trace,
    new_run,
    require_confirmed,
    write_config,
    write_metrics,
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

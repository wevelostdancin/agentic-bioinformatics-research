import json
import random
from pathlib import Path

from agentic_bioinformatics_research.repro import (
    TokenCounter,
    aggregate,
    aggregate_runs,
    set_seed,
)


def test_set_seed_is_deterministic():
    set_seed(7)
    a = [random.random() for _ in range(3)]
    set_seed(7)
    b = [random.random() for _ in range(3)]
    assert a == b


def test_different_seeds_differ():
    set_seed(1)
    a = [random.random() for _ in range(3)]
    set_seed(2)
    b = [random.random() for _ in range(3)]
    assert a != b


def test_aggregate_reports_mean_std_ci():
    r = aggregate([2, 4, 6, 8])
    assert r["mean"] == 5 and r["n"] == 4
    assert r["ci_low"] is not None and r["ci_low"] < r["mean"] < r["ci_high"]


def test_aggregate_single_value_has_no_ci():
    assert aggregate([5])["ci_low"] is None


def test_token_counter_accumulates():
    counter = TokenCounter()
    counter.add(10, 3)
    counter.add(5, 2)
    assert counter.as_dict() == {"in_tokens": 15, "out_tokens": 5}


def test_aggregate_empty_returns_no_data():
    assert aggregate([])["mean"] is None


def test_aggregate_runs_skips_missing_findings(tmp_path):
    _write_run(tmp_path, "a", {"findings": 3})
    _write_run(tmp_path, "b", {"other": 1})
    assert aggregate_runs(tmp_path, "exp")["n"] == 1


def test_aggregate_runs_filters_by_git_sha(tmp_path):
    _write_run(tmp_path, "a", {"findings": 3}, git_sha="1" * 40)
    _write_run(tmp_path, "b", {"findings": 7}, git_sha="2" * 40)
    result = aggregate_runs(tmp_path, "exp", git_sha="2" * 40)
    assert result["n"] == 1 and result["mean"] == 7


def _write_run(base: Path, name: str, metrics: dict, git_sha: str = "0" * 40) -> None:
    run_dir = base / "exp" / "runs" / name
    run_dir.mkdir(parents=True)
    (run_dir / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    (run_dir / "config.yaml").write_text(
        f'git_sha: "{git_sha}"\n', encoding="utf-8"
    )

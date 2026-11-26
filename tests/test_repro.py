import json
import random
from pathlib import Path

import pytest

from agentic_bioinformatics_research.repro import (
    TokenCounter,
    aggregate,
    aggregate_runs,
    critical_t,
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


def _write_run(
    base: Path,
    name: str,
    metrics: dict,
    git_sha: str = "0" * 40,
    extra: dict | None = None,
) -> None:
    run_dir = base / "exp" / "runs" / name
    run_dir.mkdir(parents=True)
    (run_dir / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    config = {"git_sha": git_sha, **(extra or {})}
    (run_dir / "config.yaml").write_text(
        "".join(f"{key}: {json.dumps(value)}\n" for key, value in config.items()),
        encoding="utf-8",
    )


def test_critical_t_matches_table():
    assert critical_t(2) == pytest.approx(12.706)
    assert critical_t(5) == pytest.approx(2.776)
    assert critical_t(100) == 1.96


def test_critical_t_rejects_single_observation():
    with pytest.raises(ValueError):
        critical_t(1)


def test_aggregate_uses_student_t_for_small_n():
    result = aggregate([1, 2, 3])
    assert result["ci_high"] - result["mean"] == pytest.approx(4.303 / 3**0.5, rel=1e-3)


def test_aggregate_runs_uses_custom_metric(tmp_path):
    _write_run(tmp_path, "a", {"confirmed_count": 2})
    _write_run(tmp_path, "b", {"confirmed_count": 4})
    result = aggregate_runs(tmp_path, "exp", metric="confirmed_count")
    assert result["n"] == 2 and result["mean"] == 3


def test_aggregate_runs_skips_non_numeric_metric(tmp_path):
    _write_run(tmp_path, "a", {"confirmed_count": 2})
    _write_run(tmp_path, "b", {"confirmed_count": "two"})
    assert aggregate_runs(tmp_path, "exp", metric="confirmed_count")["n"] == 1


def test_aggregate_runs_groups_by_config_factor(tmp_path):
    _write_run(tmp_path, "a", {"findings": 1}, extra={"orchestration_protocol": "debate"})
    _write_run(tmp_path, "b", {"findings": 3}, extra={"orchestration_protocol": "debate"})
    _write_run(tmp_path, "c", {"findings": 5}, extra={"orchestration_protocol": "single"})
    grouped = aggregate_runs(tmp_path, "exp", group_by=("orchestration_protocol",))
    assert set(grouped) == {"debate", "single"}
    assert grouped["debate"]["n"] == 2 and grouped["debate"]["mean"] == 2
    assert grouped["single"]["n"] == 1 and grouped["single"]["mean"] == 5

import pytest

from agentic_bioinformatics_research.metrics.cascade import (
    cascade_depth,
    decoy_uptake,
    robustness_drop,
    silent_corruption_rate,
)


def _event(agent, artifact=None, refs=()):
    return {"agent_id": agent, "artifact_id": artifact, "references": list(refs)}


def test_depth_of_chain():
    events = [
        _event("a", "f1", ["input"]),
        _event("b", "f2", ["f1"]),
        _event("c", "f3", ["f2"]),
    ]
    assert cascade_depth(events) == 3


def test_depth_without_edges_is_zero():
    assert cascade_depth([_event("a", "f1")]) == 0
    assert cascade_depth([]) == 0


def test_cycle_is_rejected():
    events = [_event("a", "f1", ["f2"]), _event("b", "f2", ["f1"])]
    with pytest.raises(ValueError):
        cascade_depth(events)


def test_decoy_uptake_counts_distinct_agents():
    events = [
        _event("a", "f1", ["decoy-1"]),
        _event("a", "f2", ["decoy-1"]),
        _event("b", "f3", ["decoy-2"]),
        _event("c", "f4", ["input"]),
    ]
    assert decoy_uptake(events, {"decoy-1", "decoy-2"}) == 2


def test_silent_corruption_rate():
    assert silent_corruption_rate(4, 3) == 0.25
    assert silent_corruption_rate(0, 0) is None


def test_silent_corruption_rejects_impossible_counts():
    with pytest.raises(ValueError):
        silent_corruption_rate(2, 3)


def test_robustness_drop():
    assert robustness_drop(1.0, 0.5) == 0.5
    assert robustness_drop(0.0, 0.0) is None

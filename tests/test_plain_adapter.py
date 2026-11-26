import pytest

from agentic_bioinformatics_research.harness import BudgetExceededError
from agentic_bioinformatics_research.harness.agents import ScriptedAgent
from agentic_bioinformatics_research.harness.plain import PlainLoopAdapter
from agentic_bioinformatics_research.metrics.cascade import cascade_depth

COUNTS = (
    "gene\tcontrol_mean\ttreated_mean\n"
    "G1\t100\t400\n"
    "G2\t50\t40\n"
    "G3\t200\t900\n"
    "G5\t10\t60\n"
    "G7\t20\t100\n"
)


def _workspace(tmp_path):
    (tmp_path / "counts.tsv").write_text(COUNTS, encoding="utf-8")
    return tmp_path


def test_single_answers_with_direct_edges(tmp_path):
    workspace = _workspace(tmp_path)
    adapter = PlainLoopAdapter(ScriptedAgent(), "single")
    result = adapter.run({"workspace": str(workspace), "budget_tokens": 10000})
    assert len(result["findings"]) == 1
    assert result["findings"][0]["references"] == ["counts.tsv"]
    assert cascade_depth([event.to_dict() for event in result["events"]]) == 1


def test_supervisor_chains_worker_claims_into_the_answer(tmp_path):
    workspace = _workspace(tmp_path)
    adapter = PlainLoopAdapter(ScriptedAgent(), "supervisor")
    result = adapter.run({"workspace": str(workspace), "budget_tokens": 10000})
    final = result["findings"][0]
    assert all(reference.startswith("worker-") for reference in final["references"])
    assert cascade_depth([event.to_dict() for event in result["events"]]) == 2


def test_budget_is_enforced(tmp_path):
    workspace = _workspace(tmp_path)
    adapter = PlainLoopAdapter(ScriptedAgent(), "single")
    with pytest.raises(BudgetExceededError):
        adapter.run({"workspace": str(workspace), "budget_tokens": 1})


def test_unsupported_protocol_is_rejected(tmp_path):
    workspace = _workspace(tmp_path)
    adapter = PlainLoopAdapter(ScriptedAgent(), "hierarchical")
    with pytest.raises(ValueError):
        adapter.run({"workspace": str(workspace), "budget_tokens": 10000})


def test_debate_runs_two_rounds_and_aggregates(tmp_path):
    workspace = _workspace(tmp_path)
    (workspace / "extra_counts.tsv").write_text(COUNTS, encoding="utf-8")
    adapter = PlainLoopAdapter(ScriptedAgent(), "debate")
    result = adapter.run({"workspace": str(workspace), "budget_tokens": 10000})
    stages = [event.role for event in result["events"]]
    assert stages.count("round1") == 2 and stages.count("round2") == 2
    assert result["findings"][0]["references"][0].startswith("debater-")
    assert cascade_depth([event.to_dict() for event in result["events"]]) >= 2


def test_tokens_are_counted(tmp_path):
    workspace = _workspace(tmp_path)
    adapter = PlainLoopAdapter(ScriptedAgent(), "supervisor")
    result = adapter.run({"workspace": str(workspace), "budget_tokens": 100000})
    assert result["tokens_in"] > 0 and result["tokens_out"] > 0

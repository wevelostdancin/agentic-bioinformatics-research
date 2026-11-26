import json

import pytest

from agentic_bioinformatics_research.harness.agents import PolzaAgent, _extract_json


def _transport(reply, usage=None):
    def call(prompt):
        assert "ROLE: analyze" in prompt or "ROLE: plan" in prompt or "ROLE: aggregate" in prompt
        return reply, usage or {"prompt_tokens": 11, "completion_tokens": 7}

    return call


def test_extract_json_tolerates_fences():
    assert _extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_rejects_prose():
    with pytest.raises(ValueError):
        _extract_json("I think the answer is G5.")


def test_analyze_reply_becomes_claims(tmp_path):
    (tmp_path / "counts.tsv").write_text("gene\n", encoding="utf-8")
    reply = json.dumps(
        {
            "claims": [
                {
                    "text": "top genes",
                    "answer": {"genes": ["G5", "G7", "G3"]},
                    "references": ["counts.tsv", "not_a_file.tsv"],
                }
            ]
        }
    )
    agent = PolzaAgent("m", transport=_transport(reply))
    result = agent("analyze", "rank genes", ["counts.tsv"], {"workspace": str(tmp_path)})
    assert result.claims[0]["answer"]["genes"] == ["G5", "G7", "G3"]
    assert result.claims[0]["references"] == ["counts.tsv"]
    assert result.tokens_in == 11 and result.tokens_out == 7


def test_plan_reply_is_filtered_to_known_files(tmp_path):
    (tmp_path / "a.tsv").write_text("x", encoding="utf-8")
    (tmp_path / "b.tsv").write_text("y", encoding="utf-8")
    reply = json.dumps({"subtasks": [{"files": ["a.tsv", "ghost.tsv"]}, {"files": ["b.tsv"]}]})
    agent = PolzaAgent("m", transport=_transport(reply))
    result = agent("plan", "split", ["a.tsv", "b.tsv"], {"workspace": str(tmp_path)})
    assert result.subtasks == [{"files": ["a.tsv"]}, {"files": ["b.tsv"]}]


def test_plan_falls_back_when_model_returns_nothing(tmp_path):
    (tmp_path / "a.tsv").write_text("x", encoding="utf-8")
    (tmp_path / "b.tsv").write_text("y", encoding="utf-8")
    agent = PolzaAgent("m", transport=_transport(json.dumps({"subtasks": []})))
    result = agent("plan", "split", ["a.tsv", "b.tsv"], {"workspace": str(tmp_path)})
    assert result.subtasks == [{"files": ["a.tsv"]}, {"files": ["b.tsv"]}]


def test_missing_key_is_reported(monkeypatch):
    monkeypatch.delenv("POLZA_API_KEY", raising=False)
    with pytest.raises(ValueError):
        PolzaAgent("m")

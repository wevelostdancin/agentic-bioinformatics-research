import json

from agentic_bioinformatics.trace import TraceEvent, append_event


def test_trace_event_has_structured_fields():
    event = TraceEvent(
        event="tool_call",
        agent_id="a1",
        role="executor",
        tool_call="grep",
        tool_args={"q": "x"},
        tokens_in=10,
        tokens_out=3,
    )
    data = event.to_dict()
    assert data["event"] == "tool_call" and data["agent_id"] == "a1"
    assert {"ts", "event_id", "tokens_in", "tokens_out", "parent_id"} <= set(data)


def test_append_event_writes_jsonl(tmp_path):
    append_event(tmp_path, TraceEvent(event="start"))
    append_event(tmp_path, TraceEvent(event="end"))
    lines = (tmp_path / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and json.loads(lines[1])["event"] == "end"

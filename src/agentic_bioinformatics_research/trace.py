import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


@dataclass
class TraceEvent:
    event: str
    ts: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    event_id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str | None = None
    role: str | None = None
    tool_call: str | None = None
    tool_args: dict | None = None
    tool_result: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    parent_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def append_event(run_dir: Path, event: TraceEvent) -> None:
    line = json.dumps(event.to_dict(), ensure_ascii=False) + "\n"
    with (run_dir / "trace.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(line)

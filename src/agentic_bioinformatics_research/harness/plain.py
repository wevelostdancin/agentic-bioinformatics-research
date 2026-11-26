from pathlib import Path

from agentic_bioinformatics_research.harness import enforce_budget
from agentic_bioinformatics_research.trace import TraceEvent


class PlainLoopAdapter:
    """Stdlib runtime for the swarm protocols.

    The adapter owns coordination only: who talks to whom, which artifact each
    claim references, and the token budget. It never writes run artifacts or
    computes metrics, so swapping in another runtime cannot change a measurement.
    """

    def __init__(self, agent, protocol: str):
        self.agent = agent
        self.protocol = protocol

    def run(self, config: dict) -> dict:
        workspace = Path(config["workspace"])
        budget = int(config["budget_tokens"])
        task = config.get("task", "")
        files = sorted(path.name for path in workspace.iterdir() if path.is_file())
        events: list[TraceEvent] = []
        tokens_in = 0
        tokens_out = 0

        def call(role: str, selected: list[str], context: dict):
            nonlocal tokens_in, tokens_out
            reply = self.agent(role, task, selected, context)
            tokens_in += reply.tokens_in
            tokens_out += reply.tokens_out
            enforce_budget({"in_tokens": tokens_in, "out_tokens": tokens_out}, budget)
            return reply

        if self.protocol == "single":
            reply = call("analyze", files, {"workspace": str(workspace), "claims": []})
            findings = self._record(events, "single", reply.claims, "answer", reply)
        elif self.protocol == "supervisor":
            plan = call("plan", files, {"workspace": str(workspace), "claims": []})
            partial: list[dict] = []
            for index, subtask in enumerate(plan.subtasks):
                reply = call(
                    "analyze",
                    subtask["files"],
                    {"workspace": str(workspace), "claims": []},
                )
                partial.extend(
                    self._record(events, f"worker-{index}", reply.claims, "partial", reply)
                )
            reply = call("aggregate", files, {"workspace": str(workspace), "claims": partial})
            findings = self._record(events, "supervisor", reply.claims, "answer", reply)
        elif self.protocol == "debate":
            half = max(1, len(files) // 2)
            groups = [files[:half], files[half:]]
            first: list[dict] = []
            for index, group in enumerate(groups):
                reply = call(
                    "analyze", group, {"workspace": str(workspace), "claims": []}
                )
                first.extend(
                    self._record(events, f"debater-{index}", reply.claims, "round1", reply)
                )
            revised: list[dict] = []
            for index, group in enumerate(groups):
                peer = [
                    claim
                    for claim in first
                    if not claim["artifact_id"].startswith(f"debater-{index}-")
                ]
                reply = call(
                    "analyze", group, {"workspace": str(workspace), "claims": peer}
                )
                revised.extend(
                    self._record(events, f"debater-{index}", reply.claims, "round2", reply)
                )
            reply = call("aggregate", files, {"workspace": str(workspace), "claims": revised})
            findings = self._record(events, "debate", reply.claims, "answer", reply)
        else:
            raise ValueError(
                f"protocol not supported by the plain loop: {self.protocol!r}"
            )

        return {
            "findings": findings,
            "events": events,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
        }

    @staticmethod
    def _record(events, agent_id, claims, stage, reply) -> list[dict]:
        recorded = []
        for index, claim in enumerate(claims):
            artifact_id = f"{agent_id}-{stage}-{index}"
            events.append(
                TraceEvent(
                    event="finding",
                    agent_id=agent_id,
                    role=stage,
                    artifact_id=artifact_id,
                    references=tuple(claim.get("references", ())),
                )
            )
            recorded.append({**claim, "artifact_id": artifact_id})
        if recorded:
            events[-1].tokens_in = reply.tokens_in
            events[-1].tokens_out = reply.tokens_out
        return recorded

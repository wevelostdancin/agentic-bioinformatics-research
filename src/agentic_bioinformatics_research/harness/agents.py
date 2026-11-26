import json
import math
from dataclasses import dataclass, field
from pathlib import Path

THRESHOLD = 1.0
TOP = 3


@dataclass
class AgentReply:
    claims: list[dict] = field(default_factory=list)
    subtasks: list[dict] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0


def _tokens(text: str) -> int:
    return max(1, len(text) // 4)


def read_counts(path: Path) -> list[tuple[str, float, float]]:
    rows = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return rows
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        try:
            rows.append((parts[0], float(parts[1]), float(parts[2])))
        except ValueError:
            continue
    return rows


def fold_changes(rows: list[tuple[str, float, float]]) -> dict[str, float]:
    return {
        gene: math.log2((treated + 1) / (control + 1))
        for gene, control, treated in rows
    }


def top_genes(
    scores: dict[str, float], threshold: float = THRESHOLD, limit: int = TOP
) -> list[str]:
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [gene for gene, score in ranked if score > threshold][:limit]


class ScriptedAgent:
    """Deterministic stand-in for a model.

    It runs a fixed fold-change analysis over whatever files it is handed and is
    deliberately naive about which files are relevant, so decoys and truncation
    affect it the way they would affect an unwary agent. It is not a model and
    its answers are not a measurement of model behaviour.
    """

    def __call__(
        self, role: str, task: str, files: list[str], context: dict
    ) -> AgentReply:
        prompt = f"{role}: {task} files={files}"
        if role == "plan":
            half = max(1, len(files) // 2)
            subtasks = [{"files": files[:half]}, {"files": files[half:]}]
            return AgentReply(
                subtasks=subtasks,
                tokens_in=_tokens(prompt),
                tokens_out=_tokens(str(subtasks)),
            )
        if role == "analyze":
            return self._analyze(prompt, files, context)
        if role == "aggregate":
            return self._aggregate(prompt, context)
        raise ValueError(f"unknown role: {role!r}")

    def _analyze(self, prompt: str, files: list[str], context: dict) -> AgentReply:
        workspace = Path(context["workspace"])
        scores: dict[str, float] = {}
        used = []
        for name in files:
            if not name.endswith("counts.tsv"):
                continue
            rows = read_counts(workspace / name)
            if not rows:
                continue
            scores.update(fold_changes(rows))
            used.append(name)
        answer = {"genes": top_genes(scores)}
        claim = {
            "text": "up-regulated genes: " + ", ".join(answer["genes"]),
            "answer": answer,
            "scores": scores,
            "references": used,
        }
        return AgentReply(
            claims=[claim],
            tokens_in=_tokens(prompt),
            tokens_out=_tokens(json.dumps(answer)),
        )

    def _aggregate(self, prompt: str, context: dict) -> AgentReply:
        scores: dict[str, float] = {}
        references = []
        for claim in context["claims"]:
            scores.update(claim.get("scores", {}))
            if claim.get("artifact_id"):
                references.append(claim["artifact_id"])
        answer = {"genes": top_genes(scores)}
        claim = {
            "text": "merged up-regulated genes: " + ", ".join(answer["genes"]),
            "answer": answer,
            "scores": scores,
            "references": references,
        }
        return AgentReply(
            claims=[claim],
            tokens_in=_tokens(prompt),
            tokens_out=_tokens(json.dumps(answer)),
        )

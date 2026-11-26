import json
import math
import os
import urllib.error
import urllib.request
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


SYSTEM_PROMPT = (
    "You are a bioinformatics agent inside a controlled experiment. "
    "Answer only with a single JSON object, no prose and no code fences."
)


def _extract_json(text: str) -> dict:
    body = text.strip()
    if body.startswith("```"):
        body = body.strip("`")
        body = body.split("\n", 1)[1] if "\n" in body else body
    start, end = body.find("{"), body.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"no JSON object in reply: {text[:200]!r}")
    return json.loads(body[start : end + 1])


class PolzaAgent:
    """Model-backed agent over an OpenAI-compatible chat completions endpoint.

    The transport is injectable, so the parsing and prompt logic is testable
    without network access.
    """

    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 90,
        transport=None,
    ):
        self.model = model
        self.base_url = (
            base_url or os.environ.get("POLZA_BASE_URL") or "https://polza.ai/api/v1"
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("POLZA_API_KEY", "")
        self.timeout = timeout
        self.transport = transport or self._http
        if transport is None and not self.api_key:
            raise ValueError("POLZA_API_KEY is not set")

    def __call__(self, role, task, files, context) -> AgentReply:
        prompt = self._prompt(role, task, files, context)
        text, usage = self.transport(prompt)
        try:
            data = _extract_json(text)
        except ValueError:
            repair = (
                prompt
                + "\n\nYour previous reply was not valid JSON. Reply with one JSON "
                "object only, no prose."
            )
            text, usage = self.transport(repair)
            data = _extract_json(text)
        tokens_in = int(usage.get("prompt_tokens", 0))
        tokens_out = int(usage.get("completion_tokens", 0))
        if role == "plan":
            subtasks = data.get("subtasks") or []
            subtasks = [
                {"files": [name for name in item.get("files", []) if name in files]}
                for item in subtasks
            ]
            subtasks = [item for item in subtasks if item["files"]]
            if not subtasks:
                half = max(1, len(files) // 2)
                subtasks = [{"files": files[:half]}, {"files": files[half:]}]
            return AgentReply(subtasks=subtasks, tokens_in=tokens_in, tokens_out=tokens_out)
        claims = data.get("claims")
        if not isinstance(claims, list) or not claims:
            claims = [{"text": "no claims returned", "answer": {}, "abstained": True}]
        allowed = (
            {claim.get("artifact_id") for claim in context.get("claims", [])}
            if role == "aggregate"
            else set(files)
        )
        clean = []
        for claim in claims:
            answer = claim.get("answer") or {}
            references = [name for name in claim.get("references", []) if name in allowed]
            clean.append(
                {
                    "text": str(claim.get("text", "")),
                    "answer": answer,
                    "scores": claim.get("scores", {}),
                    "references": references,
                    "abstained": bool(claim.get("abstained", False)),
                }
            )
        return AgentReply(claims=clean, tokens_in=tokens_in, tokens_out=tokens_out)

    def _prompt(self, role: str, task: str, files: list[str], context: dict) -> str:
        workspace = Path(context["workspace"])
        listing = []
        for name in files:
            try:
                body = (workspace / name).read_text(encoding="utf-8", errors="replace")[:2000]
            except OSError:
                body = "<unreadable>"
            listing.append(f"--- {name} ---\n{body}")
        parts = [f"ROLE: {role}", f"TASK:\n{task}", "FILES:\n" + "\n".join(listing)]
        if role == "plan":
            parts.append(
                'Return {"subtasks": [{"files": ["<name>", ...]}, ...]} splitting the '
                "available files between at most three workers."
            )
        elif role == "analyze":
            peer = context.get("claims") or []
            if peer:
                parts.append(
                    "PEER CLAIMS FROM THE OTHER DEBATER:\n"
                    + json.dumps(peer, ensure_ascii=False)[:3000]
                )
                parts.append(
                    "Revise your answer if the peer claim is better supported, and "
                    "cite only the files you actually used."
                )
            parts.append(
                'Return {"claims": [{"text": "...", "answer": {"genes": [...]}, '
                '"references": ["<file you actually used>", ...]}]}. '
                "Put the final ranked list in answer.genes. If the data is "
                "unreadable or you cannot answer, return one claim with "
                '"abstained": true and an empty answer instead of guessing.'
            )
        else:
            previous = json.dumps(context.get("claims", []), ensure_ascii=False)[:4000]
            parts.append(f"WORKER CLAIMS:\n{previous}")
            parts.append(
                'Merge the worker claims and return {"claims": [{"text": "...", '
                '"answer": {"genes": [...]}, "references": ["<worker artifact id>", ...]}]}.'
            )
        return "\n\n".join(parts)

    def _http(self, prompt: str) -> tuple[str, dict]:
        try:
            text, usage = self._request(prompt, json_mode=True)
        except urllib.error.HTTPError as error:
            if error.code != 400:
                raise
            return self._request(prompt, json_mode=False)
        except (TimeoutError, urllib.error.URLError):
            return self._request(prompt, json_mode=False)
        if not text.strip():
            # Some providers answer an empty body when JSON mode is forced.
            return self._request(prompt, json_mode=False)
        return text, usage

    def _request(self, prompt: str, json_mode: bool) -> tuple[str, dict]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            # Reasoning models spend this budget on hidden tokens first; too small
            # a cap leaves an empty or truncated answer.
            "max_tokens": 3000,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "ignore")[:300]
            raise RuntimeError(f"provider error {error.code}: {detail}") from error
        text = payload["choices"][0]["message"]["content"]
        return text, payload.get("usage") or {}


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

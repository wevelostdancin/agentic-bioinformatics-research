from dataclasses import dataclass
from pathlib import Path

# Единственный источник правды: класс -> является исполняемым доказательством.
_EVIDENCE: dict[str, bool] = {
    "hypothesis": False,
    "code_reference": False,
    "static_analyzer": False,
    "reference_match": True,
    "reproducible_test": True,
    "reproducible_poc": True,
    "sanitizer_crash": True,
    "ground_truth": True,
}
EVIDENCE_CLASSES: tuple[str, ...] = tuple(_EVIDENCE)


@dataclass(frozen=True)
class Evidence:
    evidence_class: str
    artifact: Path
    command: str
    exit_code: int


def require_confirmed(evidence: Evidence) -> None:
    if not _EVIDENCE.get(evidence.evidence_class, False):
        raise ValueError(f"{evidence.evidence_class!r} is not an executable proof")
    if not evidence.artifact.is_file():
        raise FileNotFoundError(f"evidence artifact not found: {evidence.artifact}")
    if not evidence.command.strip():
        raise ValueError("executable proof requires a command")
    if evidence.exit_code != 0:
        raise ValueError(f"proof command exited with {evidence.exit_code}")

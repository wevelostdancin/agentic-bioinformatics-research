import hashlib
import json
import random
import shutil
from pathlib import Path

PERTURBATIONS: tuple[str, ...] = (
    "none",
    "prompt_bloat",
    "corrupted_inputs",
    "decoy_files",
)

_DATA_SUFFIXES = (".tsv", ".csv", ".fa", ".fasta", ".fastq", ".vcf", ".gtf", ".bed")

_BLOAT_SENTENCES = (
    "An earlier run of this cohort used a different aligner, so the counts may drift slightly.",
    "The wet-lab team asked whether batch correction was applied before normalisation.",
    "Reference annotations were rebuilt twice, and the second build is not in this workspace.",
    "Someone noted that the sample sheet once contained a duplicate lane identifier.",
    "The previous analyst preferred a stricter mapping quality threshold than the default.",
    "A reviewer asked for a sensitivity analysis with a different normalisation method.",
    "There is a known issue with adapter contamination in the third sequencing batch.",
    "The pipeline was originally written for paired-end reads and later adapted for single-end.",
    "One collaborator suggested checking the strandedness flag before counting features.",
    "The archive contains an older annotation release that should not be used for this task.",
)

_DECOY_FILES: dict[str, str] = {
    "sample_OTHER_counts.tsv": "gene\tcount\nENSG000001\t17\nENSG000002\t4\n",
    "reference_GRCh99.fa": ">chr1_GRCh99\nACGTACGTACGTACGTACGT\n",
    "batch_2024_qc.txt": "batch\tstatus\n2024-01\tpass\n2024-02\tflagged\n",
    "old_run_notes.md": "# Legacy run\n\nThis run used the deprecated pipeline v0.9.\n",
    "sample_sheet_backup.csv": "sample,lane,index\ns9,L002,ACGT\n",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _manifest(kind: str, seed: int, changes: list[dict]) -> dict:
    canonical = json.dumps(changes, sort_keys=True, ensure_ascii=False)
    return {
        "kind": kind,
        "seed": seed,
        "changes": changes,
        "sha256": _sha256(canonical.encode("utf-8")),
    }


def _bloat(target: Path, rng: random.Random) -> dict:
    path = target / "CONTEXT_BLOAT.md"
    body = "\n".join(rng.choice(_BLOAT_SENTENCES) for _ in range(120))
    path.write_text(body + "\n", encoding="utf-8")
    return {
        "path": path.name,
        "action": "added",
        "detail": f"{len(body)} characters of irrelevant context",
    }


def _corrupt(target: Path, rng: random.Random) -> list[dict]:
    candidates = sorted(
        path for path in target.rglob("*") if path.is_file() and path.suffix in _DATA_SUFFIXES
    )
    if not candidates:
        candidates = sorted(path for path in target.rglob("*") if path.is_file())
    rng.shuffle(candidates)
    count = max(1, len(candidates) // 2)
    changes = []
    for path in candidates[:count]:
        original = path.read_bytes()
        cut = max(1, len(original) // 2)
        rewritten = original[:cut] + b"\x00" * 8
        path.write_bytes(rewritten)
        changes.append(
            {
                "path": str(path.relative_to(target)),
                "action": "corrupted",
                "detail": "truncated at 50% and padded with NUL bytes",
                "sha256_before": _sha256(original),
                "sha256_after": _sha256(rewritten),
            }
        )
    return changes


def _decoys(target: Path, rng: random.Random) -> list[dict]:
    pool = sorted(_DECOY_FILES)
    chosen = sorted(rng.sample(pool, rng.randint(2, len(pool))))
    changes = []
    for name in chosen:
        (target / name).write_text(_DECOY_FILES[name], encoding="utf-8")
        changes.append(
            {"path": name, "action": "added", "detail": "plausible but irrelevant input"}
        )
    return changes


def apply_perturbation(kind: str, source: Path, target: Path, seed: int) -> dict:
    """Copy a task tree and inject one perturbation deterministically.

    The source tree is never modified. The returned manifest lists every change
    and hashes the list, so a run can record exactly which perturbation it saw.
    """
    if kind not in PERTURBATIONS:
        raise ValueError(f"unknown perturbation: {kind!r}")
    if target.exists():
        raise FileExistsError(f"target already exists: {target}")
    shutil.copytree(source, target)
    rng = random.Random(seed)
    changes: list[dict] = []
    if kind == "prompt_bloat":
        changes.append(_bloat(target, rng))
    elif kind == "corrupted_inputs":
        changes.extend(_corrupt(target, rng))
    elif kind == "decoy_files":
        changes.extend(_decoys(target, rng))
    return _manifest(kind, seed, changes)

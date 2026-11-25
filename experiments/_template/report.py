from pathlib import Path

from agentic_bioinformatics.provenance import snapshot
from agentic_bioinformatics.repro import aggregate_runs

ROOT = Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    exp = Path(__file__).resolve().parent.name
    git_sha = snapshot(ROOT, {})["git_sha"]
    print(aggregate_runs(ROOT / "experiments", exp, git_sha=git_sha))

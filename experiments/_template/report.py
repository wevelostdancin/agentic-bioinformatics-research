from pathlib import Path

from agentic_bioinformatics.repro import aggregate_runs

ROOT = Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    print(aggregate_runs(ROOT / "experiments", "_template"))

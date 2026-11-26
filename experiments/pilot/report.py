from pathlib import Path

from agentic_bioinformatics_research.repro import aggregate_runs

ROOT = Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    exp = Path(__file__).resolve().parent.name
    # A pilot aggregates runs made across small code edits, so it is not filtered by git_sha.
    for metric in ("silent_corruption_rate", "cascade_depth", "decoy_uptake"):
        grouped = aggregate_runs(
            ROOT / "experiments",
            exp,
            metric=metric,
            group_by=("orchestration_protocol", "perturbation"),
        )
        print(f"== {metric}")
        for key, value in grouped.items():
            print(f"  {key}: n={value['n']} mean={value['mean']}")

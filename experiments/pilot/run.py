import json
from pathlib import Path

import yaml

from agentic_bioinformatics_research.harness.agents import (
    ScriptedAgent,
    fold_changes,
    read_counts,
    top_genes,
)
from agentic_bioinformatics_research.harness.plain import PlainLoopAdapter
from agentic_bioinformatics_research.matrix import expand_matrix
from agentic_bioinformatics_research.metrics.cascade import (
    cascade_depth,
    decoy_uptake,
    silent_corruption_rate,
)
from agentic_bioinformatics_research.perturbations import apply_perturbation
from agentic_bioinformatics_research.provenance import require_valid_run, snapshot
from agentic_bioinformatics_research.repro import set_seed
from agentic_bioinformatics_research.run import (
    new_run,
    write_config,
    write_metrics,
    write_summary,
)
from agentic_bioinformatics_research.trace import append_event

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.yaml"
TASK = HERE / "task"


def build_agent(name: str):
    if name == "scripted":
        return ScriptedAgent()
    raise ValueError(f"unknown agent: {name!r}")


def expected_genes() -> list[str]:
    return top_genes(fold_changes(read_counts(TASK / "counts.tsv")))


def run_cell(base_config, cell, truth):
    config = dict(base_config)
    config.update(cell)
    seed = int(config["seed"])
    set_seed(seed)
    run_dir = new_run(config["name"], seed, base=ROOT / "experiments")
    workspace = run_dir / "workspace"
    manifest = apply_perturbation(config["perturbation"], TASK, workspace, seed)
    config.update(snapshot(ROOT, config))
    config["perturbation_sha256"] = manifest["sha256"]
    write_config(run_dir, config)
    (run_dir / "perturbation.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    adapter = PlainLoopAdapter(
        build_agent(config["agent"]), config["orchestration_protocol"]
    )
    result = adapter.run(
        {
            "workspace": str(workspace),
            "budget_tokens": int(config["budget_tokens"]),
            "task": (TASK / "task.md").read_text(encoding="utf-8"),
        }
    )
    for event in result["events"]:
        append_event(run_dir, event)

    decoys = (
        {change["path"] for change in manifest["changes"]}
        if config["perturbation"] == "decoy_files"
        else set()
    )
    trace = [event.to_dict() for event in result["events"]]
    findings = len(result["findings"])
    correct = sum(
        1
        for claim in result["findings"]
        if claim.get("answer", {}).get("genes") == truth
    )
    write_metrics(
        run_dir,
        {
            "findings": findings,
            "confirmed_count": findings,
            "correct_count": correct,
            "silent_corruption_rate": silent_corruption_rate(findings, correct),
            "cascade_depth": cascade_depth(trace),
            "decoy_uptake": decoy_uptake(trace, decoys),
            "evidence_class": config.get("evidence_class", "hypothesis"),
            "tokens_used": {
                "in_tokens": result["tokens_in"],
                "out_tokens": result["tokens_out"],
            },
            "adapter": config["adapter"],
            "agent": config["agent"],
        },
    )
    answer = result["findings"][0].get("answer", {}).get("genes") if findings else []
    write_summary(
        run_dir,
        "\n".join(
            [
                f"# {config['name']}",
                "",
                "SCRIPTED AGENT: deterministic stand-in, not a model. These numbers",
                "validate the harness, not LLM behaviour.",
                "",
                f"- protocol: {config['orchestration_protocol']}",
                f"- perturbation: {config['perturbation']} ({manifest['sha256'][:12]})",
                f"- seed: {seed}",
                f"- answer: {answer}",
                f"- truth: {truth}",
                f"- cascade depth: {cascade_depth(trace)}",
            ]
        ),
    )
    require_valid_run(run_dir)
    return run_dir


def main():
    base_config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    truth = expected_genes()
    cells = expand_matrix(base_config["matrix"])
    produced = [run_cell(base_config, cell, truth) for cell in cells]
    runs = ROOT / "experiments" / base_config["name"] / "runs"
    print(f"{len(produced)} runs written to {runs}")
    return produced


if __name__ == "__main__":
    main()

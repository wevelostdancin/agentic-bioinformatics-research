import hashlib
import json
import random
from pathlib import Path

import yaml

from agentic_bioinformatics_research.harness import enforce_budget
from agentic_bioinformatics_research.matrix import expand_matrix
from agentic_bioinformatics_research.metrics.cascade import (
    cascade_depth,
    decoy_uptake,
    silent_corruption_rate,
)
from agentic_bioinformatics_research.perturbations import apply_perturbation
from agentic_bioinformatics_research.provenance import require_valid_run, snapshot
from agentic_bioinformatics_research.repro import TokenCounter, set_seed
from agentic_bioinformatics_research.run import (
    new_run,
    write_config,
    write_metrics,
    write_summary,
)
from agentic_bioinformatics_research.trace import TraceEvent, append_event

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.yaml"
TASK = HERE / "task"


def stub_swarm(protocol, workspace, rng, decoy_ids):
    """Deterministic placeholder for a real harness adapter.

    Emits a trace and findings so the pipeline runs without model calls. The
    outcome does not depend on the protocol, so any protocol difference here is
    noise by construction.
    """
    inputs = sorted(
        path.name
        for path in workspace.iterdir()
        if path.is_file() and path.name not in decoy_ids
    )
    findings = rng.randint(1, 3)
    correct = rng.randint(0, findings)
    counter = TokenCounter()
    events = []
    for index in range(findings):
        references = []
        if inputs:
            references.append(rng.choice(inputs))
        if decoy_ids and rng.random() < 0.3:
            references.append(rng.choice(sorted(decoy_ids)))
        counter.add(120, 30)
        events.append(
            TraceEvent(
                event="finding",
                agent_id=f"{protocol}-{index % 2}",
                role="executor",
                artifact_id=f"finding-{index}",
                references=tuple(references),
                tokens_in=120,
                tokens_out=30,
            )
        )
    return events, findings, correct, counter


def run_cell(base_config, cell):
    config = dict(base_config)
    config.update(cell)
    seed = int(config["seed"])
    set_seed(seed)
    run_dir = new_run(config["name"], seed, base=ROOT / "experiments")
    manifest = apply_perturbation(
        config["perturbation"], TASK, run_dir / "workspace", seed
    )
    config.update(snapshot(ROOT, config))
    config["perturbation_sha256"] = manifest["sha256"]
    write_config(run_dir, config)
    (run_dir / "perturbation.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    decoys = (
        {change["path"] for change in manifest["changes"]}
        if config["perturbation"] == "decoy_files"
        else set()
    )
    cell_key = (
        f"{seed}|{config['orchestration_protocol']}|{config['perturbation']}"
    )
    cell_seed = int.from_bytes(hashlib.sha256(cell_key.encode()).digest()[:8], "big")
    events, findings, correct, counter = stub_swarm(
        config["orchestration_protocol"],
        run_dir / "workspace",
        random.Random(cell_seed),
        decoys,
    )
    for event in events:
        append_event(run_dir, event)
    enforce_budget(counter.as_dict(), int(config["budget_tokens"]))
    trace = [event.to_dict() for event in events]
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
            "tokens_used": counter.as_dict(),
            "adapter": config["adapter"],
        },
    )
    write_summary(
        run_dir,
        "\n".join(
            [
                f"# {config['name']}",
                "",
                "STUB ADAPTER: these numbers exercise the pipeline and are not measurements.",
                "",
                f"- protocol: {config['orchestration_protocol']}",
                f"- perturbation: {config['perturbation']} ({manifest['sha256'][:12]})",
                f"- seed: {seed}",
                f"- confirmed: {findings}, correct: {correct}",
            ]
        ),
    )
    require_valid_run(run_dir)
    return run_dir


def main():
    base_config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    cells = expand_matrix(base_config["matrix"])
    produced = [run_cell(base_config, cell) for cell in cells]
    runs = ROOT / "experiments" / base_config["name"] / "runs"
    print(f"{len(produced)} runs written to {runs}")
    return produced


if __name__ == "__main__":
    main()

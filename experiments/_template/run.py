import os
from pathlib import Path

import yaml

from agentic_bioinformatics.provenance import require_valid_run, snapshot
from agentic_bioinformatics.repro import TokenCounter, set_seed
from agentic_bioinformatics.run import (
    new_run,
    write_config,
    write_metrics,
    write_summary,
)
from agentic_bioinformatics.trace import TraceEvent, append_event

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path(__file__).with_name("config.yaml")


def main() -> Path:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    seed = int(os.environ.get("SEED", config["seed"]))
    config["seed"] = seed
    set_seed(seed)
    counter = TokenCounter()
    config.update(snapshot(ROOT, config))
    run_dir = new_run(config["name"], seed, base=ROOT / "experiments")
    write_config(run_dir, config)
    append_event(
        run_dir,
        TraceEvent(
            event="start",
            agent_id="template",
            role="executor",
            tool_result=f"model={config['model']}, seed={seed}",
        ),
    )
    write_metrics(
        run_dir,
        {
            "budget_tokens": config["budget_tokens"],
            "findings": 0,
            "confirmed_count": 0,
            "evidence_class": config.get("evidence_class", "hypothesis"),
            "repetition": seed,
            "tokens_used": counter.as_dict(),
        },
    )
    write_summary(run_dir, f"# {config['name']}\n\nПрогон завершён, находок: 0.")
    require_valid_run(run_dir)
    return run_dir


if __name__ == "__main__":
    print(main())

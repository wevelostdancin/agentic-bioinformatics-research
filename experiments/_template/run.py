from pathlib import Path

import yaml

from agentic_bioinformatics.run import (
    append_trace,
    new_run,
    write_config,
    write_metrics,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path(__file__).with_name("config.yaml")


def main() -> Path:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    run_dir = new_run(config["name"], config["seed"], base=ROOT / "experiments")
    write_config(run_dir, config)
    append_trace(run_dir, {"event": "start", "model": config["model"]})
    write_metrics(run_dir, {"budget_tokens": config["budget_tokens"], "findings": 0})
    return run_dir


if __name__ == "__main__":
    print(main())

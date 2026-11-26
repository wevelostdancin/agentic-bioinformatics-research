# Agentic Bioinformatics Research

[![CI](https://github.com/wevelostdancin/agentic-bioinformatics-research/actions/workflows/ci.yml/badge.svg)](https://github.com/wevelostdancin/agentic-bioinformatics-research/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](pyproject.toml)

A reproducible research environment for studying **LLM-based multi-agent systems (MAS)**
in agentic bioinformatics. It focuses on three questions: how to orchestrate an agent
team, how to verify its findings, and how to estimate how much of the search space
remains uncovered.

> **Status:** active scaffold. The reproducibility core is implemented and tested;
> benchmark datasets and concrete agent implementations are not included yet (see Roadmap).

## Quickstart

```bash
uv sync
make check                          # ruff + pytest
make run EXP=_template              # single run
make sweep EXP=_template SEEDS=1,2,3
uv run python experiments/_template/report.py
```

Python 3.13 is pinned in `.python-version`; dependencies are locked in `uv.lock`.
No global package installation is required or allowed.

On a fresh machine, `make bootstrap` performs the whole setup in one command.
See [ENVIRONMENT.md](docs/ENVIRONMENT.md) for the portability checklist and
[data/manifest.yaml](data/manifest.yaml) for the pinned benchmark and data hashes.

## Reproducibility conventions

- A run writes four artifacts to `experiments/<exp>/runs/<UTC-timestamp>-<seed>/`:
  `config.yaml`, `trace.jsonl`, `metrics.json`, `summary.md`.
- `config.yaml` records model and harness versions, git SHA, `uv.lock` hash,
  input-data hashes, prompt/tool versions, seed, token usage and the
  `orchestration_protocol` under test.
- `git_dirty` records whether the working tree matched the recorded commit;
  `require_valid_run(..., require_clean=True)` rejects runs made from a dirty tree.
- `set_seed()` actually seeds the RNG; sweeps aggregate 3–5 repetitions as
  mean ± confidence interval rather than reporting a single run. Intervals use the
  Student-t critical value for the sample size, not the normal 1.96 approximation,
  which understates the interval below roughly 30 repetitions.
- `budget_tokens` is enforced by `enforce_budget()`; `validate_run()` flags runs whose
  `tokens_used` exceed the declared budget.
- Structured traces contain timestamps, agent ids, tool calls, and token counts,
  so they can be annotated with the MAST failure taxonomy.
- `confirmed` status requires an `Evidence` object: a proof artifact, an executed
  command, and `exit_code == 0`. `reference_match` covers bioinformatics tasks
  validated against ground truth instead of a binary proof of concept.
- Completeness uses the Chapman capture-recapture estimator with a confidence
  interval. A zero intersection means "undefined", not "zero".
- `require_valid_run()` rejects incomplete or unproven runs.

## Repository layout

| Path | Purpose |
|---|---|
| `src/agentic_bioinformatics_research/` | Reusable core: run artifacts, provenance, evidence, metrics, judge rubric, harness protocol |
| `experiments/` | One directory per study: config, runner, runs |
| `data/raw`, `data/reference`, `data/canaries` | Immutable inputs, ground truth, injected known defects |
| `docs/superpowers/` | Design specs and implementation plans |
| `docs/literature/` | Literature map (to be populated) |
| `tests/` | Regression tests for the reproducibility core |

## Documentation

- [MUST-fixes design spec](docs/superpowers/specs/2026-11-25-reproducibility-must-fixes-design.md) — current
- [MUST-fixes implementation plan](docs/superpowers/plans/2026-11-25-reproducibility-must-fixes.md) — current
- [Initial repository design](docs/superpowers/specs/2026-11-25-agentic-bioinformatics-research-repo-design.md) — historical
- [Initial implementation plan](docs/superpowers/plans/2026-11-25-agentic-bioinformatics-research-repo.md) — historical
- [Environment and portability](docs/ENVIRONMENT.md)
- [Pinned benchmark and data manifest](data/manifest.yaml)
- [Contributing guide](CONTRIBUTING.md)

## Roadmap

1. Download BioAgent Bench data (pinned in [data/manifest.yaml](data/manifest.yaml))
   and fill in SHA256 hashes with `bash scripts/check-data.sh`.
2. Add a single-agent baseline runner and one real harness adapter (LangGraph).
3. Implement perturbation factors and judge agreement validation against manual labels.
4. Run the first 2×2 factor experiment: model strength × orchestration protocol.

## Citation

See [`CITATION.cff`](CITATION.cff). If you use this code, please cite the repository.

## License

[MIT](LICENSE) © 2026 Vitaly Pesnev

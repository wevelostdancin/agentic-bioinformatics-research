# AGENTS.md — agentic-bioinformatics-research

## Environment
- Python 3.13 via uv and `.python-version`; virtual environment in `.venv`. No global `pip install`.
- Dependencies: `uv add <pkg>` (updates `pyproject.toml` and `uv.lock`).
- Reproduce with `uv sync`. Run measurements with `.venv/bin/python`.
- In sandboxed shells set `UV_CACHE_DIR` inside the workspace.

## Verification before "done"

    make check

## Layout
- `src/agentic_bioinformatics_research/` — reusable code: `run.py`, `metrics/`, `judge/`, `harness/`, `provenance.py`, `evidence.py`, `trace.py`, `repro.py`.
- `experiments/<name>/` — one design: `config.yaml`, `run.py`, `runs/`.
- `data/raw/` — immutable inputs; `data/reference/` — ground truth; `data/canaries/` — injected known defects.
- `docs/superpowers/` — specs and plans; `docs/literature/` — literature map.
- `notebooks/` — exploration only, never a source of truth; `tests/` — checks.

## Experiments
- Run: `make run EXP=<name>`; sweep: `make sweep EXP=<name> SEEDS=1,2,3`; summary: `uv run python experiments/_template/report.py`.
- Every run writes `config.yaml` (versions, git SHA, `uv.lock` hash, data hashes), a structured `trace.jsonl` (ts/agent/tool/tokens), `metrics.json`, and `summary.md` to `experiments/<name>/runs/<timestamp>-<seed>/`.
- Apply seeds with `set_seed()`; aggregate 3–5 repetitions with `aggregate()` (mean ± CI); record `tokens_used`.
- Change one factor at a time, keep token budgets equal, and run a single-agent baseline before orchestration.

## Evidence rules
- `confirmed` requires `Evidence`: PoC, reproducible test, sanitizer crash, ground truth, or `reference_match`; a proof artifact, a command, and `exit_code == 0` are mandatory.
- `refuted` requires counter-evidence, never an LLM judge's opinion.
- Completeness is an estimate of the remainder plus explicitly uncovered cells, never a guarantee.

## Where to put specs and plans
- `docs/superpowers/specs/YYYY-MM-DD-*-design.md`
- `docs/superpowers/plans/YYYY-MM-DD-*.md`

## Rules
- Commit `uv.lock` — the environment must be reproducible.
- Secrets belong in `.env` only (gitignored); `.env.example` contains placeholders.

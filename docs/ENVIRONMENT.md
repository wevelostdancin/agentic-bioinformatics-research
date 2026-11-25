# Environment and Portability

This document describes what is pinned, how to reproduce the environment on a new
machine, and what still has to be pinned before reported results are comparable.

## What is pinned today

| Item | Source of truth |
|---|---|
| Python | `.python-version` (3.13) |
| Python packages | `uv.lock` (committed, exact versions) |
| Benchmark | `data/manifest.yaml` — BioAgent Bench at commit `6d098b6` |
| Benchmark paper | arXiv:2601.21800v4, CC-BY-4.0 |
| Model / harness versions | `config.yaml` of each run (`model_version`, `harness_version`) |
| Code state | `git_sha` in each run's `config.yaml` |
| Input data | `data_sha256` in each run's `config.yaml` |

## Fresh machine

```bash
brew install uv                       # or: curl -LsSf https://astral.sh/uv/install.sh | sh
git clone git@github.com:wevelostdancin/agentic-bioinformatics-research.git
cd agentic-bioinformatics-research
make bootstrap
```

`make bootstrap` runs `uv sync --frozen`, creates `.env` from the template if needed,
runs `make check`, and executes a smoke run. Fill `.env` with real API keys before any
study that calls a model. Never commit `.env`.

In sandboxed shells set `UV_CACHE_DIR` to a writable folder inside the workspace.

## Benchmark data

Data is not committed. `data/manifest.yaml` pins the upstream repository, commit,
license, and download command. After downloading, run `bash scripts/check-data.sh`
and paste the hashes into `file_sha256` in the manifest. Third-party datasets keep
their own licenses; attribute BioAgent Bench contributors when reusing its materials.

## What is not pinned yet

- **Bioinformatics tool containers.** When SAMtools/GATK/DESeq2 images are added, pin
  them by digest (`image@sha256:...`), never by tag. Until then, `reference_match`
  results may drift between machines.
- **Grader model snapshot.** BioAgent Bench uses GPT-5.1 as grader; record the exact
  snapshot id and prompt version in the run config when the grader is connected.
- **Real token usage.** The template's `TokenCounter` is a stub until agents make
  actual model calls.
- **Result export.** `runs/` is intentionally gitignored. Share results by archiving a
  run directory or by attaching it as a CI artifact, not by committing it.

## Pre-flight checklist before publishing a result

1. `uv lock --check` and `make check` are green.
2. The manifest contains hashes for every input file used.
3. Each run passes `require_valid_run()` and contains four artifacts.
4. Three to five seeds were run and mean ± CI is reported.
5. The command used to produce the result is recorded in the run config.

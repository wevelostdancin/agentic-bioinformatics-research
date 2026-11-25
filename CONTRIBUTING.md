# Contributing

## Development setup

```bash
uv sync
make check
```

Python 3.13 is pinned in `.python-version`. Dependencies are managed with
`uv add` / `uv lock`; never install packages into the system interpreter.
`uv.lock` is committed and must stay in sync with `pyproject.toml`.

## Workflow

1. Create a branch from `main`.
2. Write a failing test first (TDD), then implement the minimal change.
3. Run `make check` (ruff + pytest). All tests must pass.
4. Open a pull request using the template in `.github/PULL_REQUEST_TEMPLATE.md`.

## Experiment protocol

- One factor changes at a time; compare methods at an equal token budget.
- Always include a single-agent baseline before testing orchestration.
- Use 3–5 repetitions via `make sweep EXP=<name> SEEDS=1,2,3` and report
  mean ± confidence interval, not a single run.
- Every run must contain `config.yaml`, `trace.jsonl`, `metrics.json`, and
  `summary.md`; `require_valid_run()` enforces this.
- `confirmed` status requires an `Evidence` object with a proof artifact,
  an executed command, and `exit_code == 0`.
- Never commit `.env`, raw datasets, or run artifacts.

## Commit messages

Use conventional prefixes: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`.

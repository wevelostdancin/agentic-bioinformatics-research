# Initial Repository Bootstrap — Implementation Plan

> **For agentic workers:** use superpower-subagent-driven-development or superpower-executing-plans; steps use `- [ ]` checkboxes.

**Goal:** create a clean, reproducible local git repository with an isolated Python environment and a minimal core for MAS experiments in bioinformatics.

**Architecture:** the sanctioned `newproj` creates a uv project (`.venv`, `uv.lock`, ignore rules, README, AGENTS.md, git, private GitHub); a standard layout and a small reproducibility core are added on top.

**Tech stack:** bash, git, uv, Python 3.13, pytest, ruff, PyYAML, gh CLI.

**Spec:** `docs/superpowers/specs/2026-11-25-agentic-bioinformatics-research-repo-design.md` (historical).

## Global constraints

- Python 3.13 from miniforge; `.venv` inside the project; no global `pip install`.
- Dependencies only via `uv add` / `uv sync`; `uv.lock` is committed.
- Target path `~/Projects/research/agentic-bioinformatics` (later renamed).
- The empty folder with a space is removed only after its absolute path and emptiness are checked.
- Private GitHub remote; if `gh` is unavailable, the local repository still works.
- Secrets live in `.env` only (gitignored); `.env.example` contains placeholders.

## Review focus

- Unauthenticated `gh` → local repository still created, GitHub skipped without failure.
- A real `.env` never enters the git index.
- `capture_recapture` with `m == 0` must not divide by zero.
- `confirmed` must not be granted without executable evidence.
- `.venv` / `.uv-cache` must never be committed.

---

### Task 1 — Preflight and remove the empty folder

- [ ] Print absolute paths and verify the folder is empty.
- [ ] Check `uv`, `gh` authentication, Python version, and that the target path is free.
- [ ] `rmdir` the empty folder and confirm the workspace is clean.
- [ ] No commit (no repository yet).

### Task 2 — Scaffold with `newproj`

- [ ] `newproj agentic-bioinformatics --root ~/Projects/research`.
- [ ] Verify `pyproject.toml`, `uv.lock`, `.python-version`, `README.md`, `AGENTS.md`,
      `.gitignore`, `.venv`, git history, and a single bootstrap commit.
- [ ] Check `git remote -v` and `git check-ignore -v .venv`.
- [ ] The bootstrap commit is created by `newproj`.

**Ruling:** `uv init --app` created `src/agentic_bioinformatics_research` and no `main.py`;
the stale `[project.scripts]` was removed and that package became the buildable module.

### Task 3 — Copy spec/plan and add dev tooling

- [ ] Copy the spec and plan into `docs/superpowers/`.
- [ ] `uv add --dev ruff pytest pyyaml`.
- [ ] `uv run ruff check .` and `uv run pytest -q` (exit code 5 for "no tests ran" accepted at this stage).
- [ ] Commit: `docs: add spec and plan, configure dev tooling`.

**Ruling:** `UV_CACHE_DIR` was redirected into the workspace because the sandbox denies `~/.cache/uv`.

### Task 4 — Structure, AGENTS.md, README.md, Makefile

- [ ] Create `src/agentic_bioinformatics_research/{metrics,judge,harness}`, `experiments`,
      `data/{raw,reference,canaries}`, `docs/literature`, `notebooks`, `tests`.
- [ ] Add `.env.example` with placeholders; extend `.gitignore` with `.uv-cache/`,
      `runs/`, `data/raw/*`.
- [ ] Document layout, experiment protocol, evidence rules, and doc locations in AGENTS.md.
- [ ] Rewrite README with a one-line reproduction command.
- [ ] Makefile targets `check` and `run EXP=...`.
- [ ] Commit: `chore: add repo structure, docs and make targets`.

### Task 5 — Reproducibility core (TDD)

Interfaces produced:

```
new_run(exp: str, seed: int, base: Path = Path("experiments")) -> Path
write_config(run_dir: Path, config: dict) -> None
append_trace(run_dir: Path, event: dict) -> None
write_metrics(run_dir: Path, metrics: dict) -> None
write_summary(run_dir: Path, text: str) -> None
require_confirmed(evidence: str, artifact: Path) -> None
capture_recapture(n1: int, n2: int, m: int) -> float
coverage_matrix(cells, covered) -> dict
canary_recall(injected, caught) -> dict[str, float]
rubric() -> dict
HarnessAdapter (Protocol with run(config: dict) -> dict)
```

- [ ] Write failing tests for all interfaces; watch RED.
- [ ] Implement minimal code; watch GREEN (9 tests at this stage).
- [ ] Commit: `feat: add reproducibility core with tests`.

### Task 6 — Template experiment and verification

- [ ] Add `experiments/_template/config.yaml` and `run.py`.
- [ ] Run `make run EXP=_template` and verify the four artifacts.
- [ ] `make check` green; `git status` clean; `origin` present.
- [ ] Commit: `feat: add experiment template and verify reproducibility`.

**Ruling:** `new_run` uses `config['name']`, so the template config name was set to
`_template` to match the expected directory; an accidentally created stale run was
removed after verifying its absolute path.

# Design: Local Repository and Environment for LLM-Based MAS Research in Bioinformatics

Date: 2026-11-25
Status: historical — superseded by the reproducibility MUST-fixes spec

## 1. Context and goal

The user is starting research on LLM-based multi-agent systems (MAS) with a focus on
agentic bioinformatics. A clean, professional, reproducible local repository and
environment are needed for experiments on:

1. orchestrating an agent team (topology, delegation, debate, arbiter);
2. verifying findings (oracles, PoCs, evidence classes);
3. estimating coverage/completeness (capture-recapture, canaries, saturation).

**Success criterion:** on another machine (or a month later) any recorded run can be
reproduced from the documented procedure; every result has a config, a seed, a trace,
and an explicit evidence class; the environment does not depend on globally installed
packages.

## 2. Existing state and constraints

- The parent folder was not a git repository; it contained an empty directory with a
  space in its name, which was removed after verifying its absolute path and emptiness.
- Machine contract (`~/.dsh/AGENTS.md`): `python3` is miniforge 3.13; environments live
  inside projects (`.venv` / `uv sync`); global `pip install` is forbidden; lock files are
  committed; secrets are never printed or committed; absolute paths are checked before
  `rm`/`mv`.
- The user explicitly chose to create a **private GitHub repository** and push the scaffold.

## 3. Approaches considered

| Approach | Pros | Cons | Decision |
|---|---|---|---|
| `newproj <name>` | Sanctioned: uv project, `.venv`, `uv.lock`, ignore rules, README, AGENTS.md, git, GitHub in one command | Creates a remote by default (desired here) | **Chosen** |
| Manual `git init` in the existing folder | Full control | Violates the "new project only via newproj" rule; easy to forget lock/ignore | Rejected |
| Cookiecutter / research template | Ready-made layout and CI | Extra abstraction layer, incompatible with the machine contract, YAGNI | Rejected |

## 4. Design

### 4.1 Name and location

- Original project path: `~/Projects/research/agentic-bioinformatics`.
- The GitHub repository and local folder are now named `agentic-bioinformatics-research`.
- Created with `newproj agentic-bioinformatics --root ~/Projects/research`; GitHub was
  created automatically because `gh` was authenticated.

### 4.2 Environment

- Python 3.13 from miniforge; isolated `.venv` inside the project.
- `pyproject.toml` declares intent; `uv.lock` pins exact versions (committed).
- Reproduction: `uv sync`. Run measurements with `.venv/bin/python`.
- `.env.example` holds placeholders; `.env` is gitignored.

### 4.3 Structure

```
agentic-bioinformatics-research/
├── AGENTS.md / README.md / CONTRIBUTING.md / CITATION.cff / LICENSE
├── pyproject.toml / uv.lock / .python-version / .gitignore / .env.example
├── Makefile                 # check, run, sweep
├── src/agentic_bioinformatics_research/
│   ├── run.py               # run artifacts
│   ├── repro.py             # seed, aggregation, tokens
│   ├── provenance.py        # snapshot, validation
│   ├── evidence.py          # executable evidence gate
│   ├── trace.py             # structured events
│   ├── metrics/             # coverage, canaries
│   ├── judge/               # rubric, validation
│   └── harness/             # replaceable adapter protocol
├── experiments/<name>/      # config.yaml, run.py, runs/
├── data/{raw,reference,canaries}/
├── docs/{superpowers,literature}/
├── notebooks/
└── tests/
```

### 4.4 Experiment rules

- One factor at a time; equal token budget; 3–5 repetitions with different seeds;
  single-agent baseline before any orchestration.
- Each run writes `config.yaml`, `trace.jsonl`, `metrics.json`, `summary.md` into
  `experiments/<name>/runs/<timestamp>-<seed>/`.
- `confirmed` requires executable proof (PoC, test, sanitizer crash, ground truth);
  `refuted` requires counter-evidence, not an LLM judge's opinion.
- Completeness is an estimate of the remainder plus explicitly uncovered cells.

### 4.5 Harnesses

- DeepSeek Harness is the day-to-day workspace; LangGraph + BioinfoMCP are planned for
  strict experiments. Experiment code stays plain Python; the harness is a replaceable
  adapter rather than a hard dependency.

### 4.6 GitHub

- Private remote created by `newproj`; `gh repo rename` later changed the name to
  `agentic-bioinformatics-research` and the local remote URL was updated.
- If `gh` is unavailable or unauthenticated, `newproj` leaves a working local repository
  and reports the skip without failing.

### 4.7 Agent instructions

`AGENTS.md` documents environment, layout, experiment protocol, evidence rules, and
where to put specs and plans.

## 5. Out of scope

The research itself and its results; installing bioinformatics CLI tools; large datasets.

## 6. Verification

1. `newproj` exits 0 and creates the expected files.
2. `.venv/bin/python --version` → 3.13.x; `uv sync` succeeds.
3. `make check` is green; a smoke run produces all four artifacts.
4. `git status` is clean after commits; `git remote -v` shows `origin`.
5. The old folder with the space is gone.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| `gh` unauthenticated / no network | Check `gh auth status`; leave a local repo and report honestly |
| uv cache unavailable in sandbox | `UV_CACHE_DIR` inside the workspace; directory is gitignored |
| Space in the old folder name | Remove only after verifying absolute path and emptiness |
| Accidental global `pip install` | All dependencies via `uv add` / `uv sync` |

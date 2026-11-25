# Design: MUST Fixes for Reproducibility (Literature Review Follow-up)

Date: 2026-11-25
Status: approved, implemented, reviewed by two independent agents

## 1. Context

A teammate on hy4 flash compared the repository with MAST, BixBench, BioAgent Bench,
AIxCC, MoA/More Agents, Wohlin 1995, Comcast 2026, Zheng et al., and AFlow. Verdict:
the scaffold was correct but reproducibility was declarative. The user approved five
MUST fixes.

Verified locally at the time: `seed` was used only in the run directory name;
`trace.jsonl` had one event; `data/*` and `docs/literature/` contained no content;
older runs lacked the new config fields.

## 2. Goals

1. **Apply the seed**, measure variability, and account for actual tokens.
2. **Provenance snapshot and artifact validator**: each run is self-contained.
3. **Correct completeness estimation**: replace the biased estimator, make uncertainty explicit.
4. **Executable evidence**: the gate checks execution results, not labels or file presence.
5. **Trace schema and judge validation**: events annotatable with MAST; judge agreement measured.

## 3. Constraints

- Changes are confined to the repository; external actions are commits and pushes.
- TDD: a failing test precedes every new behavior.
- Existing tests stay green unless explicitly rewritten with a recorded ruling.
- No heavy dependencies: stdlib plus pytest/ruff/PyYAML.
- Machine contract: `UV_CACHE_DIR` in the workspace, project `.venv`, `make check` before "done".

## 4. Design

### 4.1 Seeds, variability, tokens — `repro.py`

- `set_seed(seed: int) -> None` seeds `random`; called by the template before any work.
- `aggregate(values: list[float]) -> dict` returns `mean`, `std`, `n`, `ci_low`, `ci_high`
  (normal approximation 1.96·SE); CI is `None` for `n < 2`.
- `TokenCounter` accumulates input/output tokens and serializes to a dict.
- Template writes `tokens_used` and `repetition`; `make sweep ... SEEDS=1,2,3` runs repeats.

### 4.2 Provenance and validation — `provenance.py`

- `snapshot(repo_root, config)` returns `git_sha`, `uv_lock_sha256`, `data_sha256`,
  `prompt_version`, `tool_versions`; it does not fail outside a git repository.
- `validate_run(run_dir) -> list[str]` checks the four artifacts, required config fields,
  valid hex hashes, a non-empty JSONL trace, and required metric fields; it never raises.
- `require_valid_run` raises with a collected message.

### 4.3 Completeness — `metrics/coverage.py`

- Chapman estimator `(n1+1)(n2+1)/(m+1)-1`; `m == 0` → `inf` (undefined, not zero).
- Inputs validated: `n1, n2 >= 0`, `0 <= m <= min(n1, n2)`.
- `capture_recapture_ci` uses the Chapman variance, clamps the lower bound to the number
  of uniquely observed items, and avoids zero-width intervals.
- `saturation_curve(counts)` returns cumulative fractions; `coverage_matrix` reports
  `uncovered_cells` explicitly. Metrics separate `findings` from `confirmed_count`.

### 4.4 Executable proof — `evidence.py`

- `Evidence(evidence_class, artifact, command, exit_code)`.
- `require_confirmed` accepts only executable classes (`reference_match`,
  `reproducible_test`, `reproducible_poc`, `sanitizer_crash`, `ground_truth`) and requires
  an existing artifact, a non-empty command, and `exit_code == 0`.
- A string wrapper remains in `run.py` but now also requires an artifact.

### 4.5 Trace and judge — `trace.py`, `judge/validation.py`

- `TraceEvent` carries `ts`, `event_id`, `agent_id`, `role`, event and tool fields,
  `tokens_in`, `tokens_out`, `parent_id`; `append_event` writes JSONL.
- `cohen_kappa` and `position_swap_agreement` quantify judge agreement; the rubric
  includes the three MAST categories.

## 5. Out of scope

Benchmark selection and data population, real agents and LLM calls, concrete
LangGraph/BioinfoMCP adapters, automated orchestration search (ADAS/AFlow).

## 6. Verification

- `make check` green; test count grew from 14 to 47.
- `make sweep EXP=_template SEEDS=1,2,3` produces three validated runs and an aggregate.
- `git status` clean after commits; `origin/main == HEAD`.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Existing tests break | Chapman expectations explicitly rewritten with a ruling |
| API gets complicated | Old functions kept as compatible wrappers |
| No real LLM call | Seed determinism and token counting tested on RNG/counter, not a model |

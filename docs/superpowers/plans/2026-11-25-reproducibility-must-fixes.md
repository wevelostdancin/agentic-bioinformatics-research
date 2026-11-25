# Reproducibility MUST Fixes — Implementation Plan

> **For agentic workers:** use superpower-executing-plans (chosen by the user); steps use `- [ ]` checkboxes.

**Goal:** turn declarative reproducibility into verifiable reproducibility: working seeds, full provenance, correct completeness estimation, executable evidence, and a MAST-ready trace.

**Architecture:** five narrow modules are added next to the existing core (`repro`,
`provenance`, `evidence`, `trace`, `judge/validation`) without rewriting `run.py`;
old APIs remain compatible wrappers.

**Tech stack:** Python 3.13 stdlib, pytest, ruff, PyYAML, uv, make, git.

**Spec:** `docs/superpowers/specs/2026-11-25-reproducibility-must-fixes-design.md`.

## Global constraints

- `UV_CACHE_DIR` is set in the workspace; checks go through `make check`.
- No new dependencies; stdlib plus already installed pytest/ruff/PyYAML.
- Existing tests stay green except explicitly rewritten Chapman expectations.
- Commits are frequent; push to the private `origin/main` after a green review.

## Review focus

- `set_seed` really determinizes RNG rather than only writing a number into config.
- `snapshot` does not crash outside git and writes no secrets into artifacts.
- `capture_recapture` returns `inf`, not a false zero, at `m == 0`.
- `require_confirmed(Evidence)` cannot grant confirmation without an artifact,
  a non-empty command, and `exit_code == 0`.
- `cohen_kappa` and `position_swap_agreement` are correct on known inputs.

---

### Task 1 — Seeds, aggregation, tokens

Produces `set_seed`, `aggregate`, `aggregate_runs`, `TokenCounter`.

- [ ] Write failing tests for determinism, different seeds, mean/std/CI, no CI for `n=1`, token accumulation; watch RED.
- [ ] Implement `repro.py`; watch GREEN.
- [ ] Integrate into the template (`SEED` environment override, `tokens_used`, `repetition`) and add `make sweep`.
- [ ] Verify `make sweep EXP=_template SEEDS=1,2,3` and `report.py`.
- [ ] Commit: `feat: apply seeds, track tokens and aggregate repetitions`.

**Ruling:** `make sweep` initially passed `1,2,3` as one word; fixed with a `comma`
variable and `$(subst $(comma), ,$(SEEDS))`. Cost: only the invocation syntax.

### Task 2 — Provenance and validator

Produces `snapshot`, `validate_run`, `require_valid_run`.

- [ ] Write failing tests for required keys, data hashes, missing artifacts, and a complete run; watch RED.
- [ ] Implement SHA256 snapshot and validation; watch GREEN.
- [ ] Add `prompt_version` / `tool_versions` to the template config and merge the snapshot
      at the top level of `config.yaml`; call `require_valid_run` after each run.
- [ ] Commit: `feat: add provenance snapshot and run validator`.

**Ruling:** the snapshot was first nested under `config['provenance']` while the validator
looked at the top level; fixed with `config.update(snapshot(...))`.

### Task 3 — Correct completeness estimation

Produces Chapman `capture_recapture`, `capture_recapture_ci`, `saturation_curve`.

- [ ] Rewrite old tests to expect `inf` at `m=0` and Chapman `121/6-1`; add CI and saturation tests; watch RED.
- [ ] Implement the estimator, variance-based CI, input validation, and cumulative curve; watch GREEN.
- [ ] Add `confirmed_count` to template metrics.
- [ ] Commit: `fix: use Chapman estimator and expose completeness uncertainty`.

### Task 4 — Executable evidence

Produces `Evidence` and a strict `require_confirmed(Evidence)`.

- [ ] Write failing tests: valid executed proof, missing artifact, failed command, missing
      command, `reference_match`; watch RED.
- [ ] Implement `evidence.py` as the single source of truth; keep a string wrapper in `run.py`; watch GREEN.
- [ ] Commit: `feat: require executed proof for confirmed evidence`.

### Task 5 — Structured traces and judge validation

Produces `TraceEvent`, `append_event`, `cohen_kappa`, `position_swap_agreement`.

- [ ] Write failing tests for structured fields, JSONL append, perfect/known kappa, swap agreement; watch RED.
- [ ] Implement modules; watch GREEN.
- [ ] Extend `rubric()` with the three MAST categories; make the template emit `TraceEvent`.
- [ ] Commit: `feat: structured traces and judge agreement validation`.

### Task 6 — Verification, review, push

- [ ] Update README/AGENTS; remove the stale run after checking its absolute path.
- [ ] `make check`, sweep, `report.py`, clean tree.
- [ ] Commit docs, push, and run an independent review.
- [ ] Fix Critical/Important findings in one RED→GREEN pass.

### Post-review fix pass (both reviewers)

- CI lower bound clamped to the number of uniquely observed items; zero-width intervals removed.
- Validator upgraded to value-level checks and graceful YAML error handling.
- Aggregation skips runs without `findings`, filters by `git_sha`, and reports `None` for empty input.
- String wrapper now requires an artifact; `EVIDENCE_CLASSES` re-exported from `run.py`.
- Commit: `fix: reject invalid runs and incomparable aggregates`.

## Deferred (not in the fix pass)

`position_swap_agreement` remains raw agreement; `snapshot` does not catch a missing `git`
binary; `bool` exit codes; `make sweep` without `set -e`; old plan checkboxes; data and
literature folders; real LLM calls and token accounting; benchmark selection.

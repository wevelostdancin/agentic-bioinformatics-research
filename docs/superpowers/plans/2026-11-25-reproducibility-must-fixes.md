# Reproducibility MUST Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpower-subagent-driven-development (recommended) or superpower-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Превратить декларативную воспроизводимость репозитория в проверяемую: рабочий seed, полный provenance-снапшот, корректная оценка полноты, исполняемые доказательства и пригодный для MAST-разметки трейс.

**Architecture:** Добавляем пять узких модулей рядом с существующим ядром (`repro`, `provenance`, `evidence`, `trace`, `judge/validation`), не переписывая `run.py` целиком; старые API остаются совместимыми обёртками. Шаблон эксперимента и Makefile становятся первой реальной реализацией новых конвенций.

**Tech Stack:** Python 3.13 stdlib, pytest, ruff, PyYAML, uv, make, git.

**Spec:** `docs/superpowers/specs/2026-11-25-reproducibility-must-fixes-design.md`

**Execution method:** Native (перенесено с предыдущего плана: задачи последовательны, план несёт все решения).

## Global Constraints

- `UV_CACHE_DIR` задаётся в рабочей папке; проверки только через `make check`.
- Новые зависимости не добавляются; только stdlib + уже установленные pytest/ruff/pyyaml.
- Существующие тесты остаются зелёными, кроме явно переписанных ожиданий Chapmanа.
- Каждый прогон по-прежнему пишет 4 артефакта; новые поля добавляются, не заменяют.
- Коммиты частые; пуш в приватный `origin/main` после зелёного ревью.

## Review Focus

- `set_seed` действительно детерминирует последовательность, а не только записывает число в конфиг (Task 1).
- `snapshot` не падает вне git-репозитория и не кладёт секреты в артефакты (Task 2).
- `capture_recapture` при `m=0` не возвращает ложное `0.0`, а сообщает неопределённость (Task 3).
- `require_confirmed` не принимает «подтверждено» без исполненной команды и существующего proof-файла (Task 4).
- `cohen_kappa` и `position_swap_agreement` дают осмысленные числа на известных входах (Task 5).

---

### Task 1: Seed, агрегация и токены

**Files:**
- Create: `src/agentic_bioinformatics/repro.py`, `tests/test_repro.py`, `experiments/_template/report.py`
- Modify: `experiments/_template/run.py`, `Makefile`

**Interfaces:**
- Produces: `set_seed(seed: int) -> None`; `aggregate(values: list[float]) -> dict`; `aggregate_runs(base: Path, exp: str) -> dict`; `TokenCounter` с `add(in_tokens: int, out_tokens: int) -> None` и `as_dict() -> dict`

- [ ] **Step 1: Написать падающие тесты** в `tests/test_repro.py`:
```python
def test_set_seed_is_deterministic():
    import random
    from agentic_bioinformatics.repro import set_seed
    set_seed(7); a = [random.random() for _ in range(3)]
    set_seed(7); b = [random.random() for _ in range(3)]
    assert a == b

def test_different_seeds_differ():
    import random
    from agentic_bioinformatics.repro import set_seed
    set_seed(1); a = [random.random() for _ in range(3)]
    set_seed(2); b = [random.random() for _ in range(3)]
    assert a != b

def test_aggregate_reports_mean_std_ci():
    from agentic_bioinformatics.repro import aggregate
    r = aggregate([2, 4, 6, 8])
    assert r["mean"] == 5 and r["n"] == 4
    assert r["ci_low"] is not None and r["ci_low"] < r["mean"] < r["ci_high"]

def test_aggregate_single_value_has_no_ci():
    from agentic_bioinformatics.repro import aggregate
    assert aggregate([5])["ci_low"] is None

def test_token_counter_accumulates():
    from agentic_bioinformatics.repro import TokenCounter
    c = TokenCounter(); c.add(10, 3); c.add(5, 2)
    assert c.as_dict() == {"in_tokens": 15, "out_tokens": 5}
```

- [ ] **Step 2: Показать RED**: `uv run pytest -q` → `ModuleNotFoundError: repro`.

- [ ] **Step 3: Реализовать** `repro.py`: `random.seed`, `statistics.fmean`/`stdev`, `1.96 * stdev/sqrt(n)`, `None` при `n<2`; `aggregate_runs` читает `metrics.json` из `base/exp/runs/*` и агрегирует поле `findings`.

- [ ] **Step 4: GREEN**: `uv run pytest -q` → все тесты зелёные.

- [ ] **Step 5: Интеграция в шаблон**: `run.py` читает `SEED` из окружения (по умолчанию из конфига), вызывает `set_seed`, пишет `tokens_used` и `repetition` в `metrics.json`; `report.py` печатает `aggregate_runs`. В `Makefile` — цель `sweep`: для каждого `SEED` из `SEEDS` вызвать `make run EXP=...`.

- [ ] **Step 6: Проверка**: `make sweep EXP=_template SEEDS=1,2,3` создаёт три прогона; `uv run python experiments/_template/report.py` печатает агрегат; `make check` зелёный.

- [ ] **Step 7: Commit**: `git commit -m "feat: apply seeds, track tokens and aggregate repetitions"`

### Task 2: Provenance и валидатор

**Files:**
- Create: `src/agentic_bioinformatics/provenance.py`, `tests/test_provenance.py`
- Modify: `experiments/_template/run.py`, `experiments/_template/config.yaml`

**Interfaces:**
- Produces: `snapshot(repo_root: Path, config: dict) -> dict`; `validate_run(run_dir: Path) -> list[str]`; `require_valid_run(run_dir: Path) -> None`

- [ ] **Step 1: Падающие тесты** в `tests/test_provenance.py`:
```python
def test_snapshot_contains_required_keys():
    from pathlib import Path
    from agentic_bioinformatics.provenance import snapshot
    root = Path(__file__).resolve().parents[1]
    s = snapshot(root, {"prompt_version": "v1"})
    assert set(s) >= {"git_sha", "uv_lock_sha256", "data_sha256", "prompt_version"}
    assert len(s["git_sha"]) == 40 and len(s["uv_lock_sha256"]) == 64

def test_snapshot_hashes_data_files(tmp_path):
    from agentic_bioinformatics.provenance import snapshot
    (tmp_path / "data/raw").mkdir(parents=True)
    (tmp_path / "data/raw/a.txt").write_text("x")
    s = snapshot(tmp_path, {})
    assert "data/raw/a.txt" in s["data_sha256"]

def test_validate_run_reports_missing_artifacts(tmp_path):
    from agentic_bioinformatics.provenance import validate_run
    issues = validate_run(tmp_path)
    assert any("config.yaml" in i for i in issues)

def test_validate_run_accepts_complete_run(tmp_path):
    from agentic_bioinformatics.provenance import validate_run
    cfg = {"model_version": "v1", "harness_version": "v1", "seed": 1,
           "git_sha": "0"*40, "uv_lock_sha256": "0"*64}
    (tmp_path / "config.yaml").write_text("x")
    (tmp_path / "trace.jsonl").write_text("")
    (tmp_path / "metrics.json").write_text("{}")
    (tmp_path / "summary.md").write_text("x")
    # тест использует yaml.safe_dump для config.yaml, чтобы проверить поля
    import yaml
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(cfg))
    assert validate_run(tmp_path) == []
```

- [ ] **Step 2: RED**: `uv run pytest -q` → `ModuleNotFoundError: provenance`.

- [ ] **Step 3: Реализовать**: `git -C <root> rev-parse HEAD` через `subprocess.run(check=False)`, при ошибке `"unknown"`; SHA256 файлов; `validate_run` проверяет 4 файла и обязательные поля в `config.yaml`.

- [ ] **Step 4: GREEN**: `uv run pytest -q`.

- [ ] **Step 5: Интеграция**: в конфиг шаблона добавить `prompt_version: v1` и `tool_versions: {}`; `run.py` кладёт `snapshot(ROOT, config)` в `config.yaml` перед записью; после прогона вызывать `require_valid_run`.

- [ ] **Step 6: Commit**: `git commit -m "feat: add provenance snapshot and run validator"`

### Task 3: Корректная оценка полноты

**Files:**
- Modify: `src/agentic_bioinformatics/metrics/coverage.py`, `tests/test_coverage.py`, `experiments/_template/run.py`

**Interfaces:**
- Produces: `capture_recapture(n1: int, n2: int, m: int) -> float`; `capture_recapture_ci(...) -> tuple[float, float]`; `saturation_curve(counts: list[int]) -> list[float]`

- [ ] **Step 1: Переписать ожидания в тестах** (RED):
```python
import math
import pytest
from agentic_bioinformatics.metrics.coverage import (
    capture_recapture, capture_recapture_ci, saturation_curve,
)

def test_capture_recapture_zero_intersection_is_undefined():
    assert capture_recapture(10, 8, 0) == float("inf")

def test_capture_recapture_chapman_estimate():
    assert capture_recapture(10, 10, 5) == pytest.approx(121 / 6 - 1)

def test_capture_recapture_rejects_impossible_m():
    with pytest.raises(ValueError):
        capture_recapture(10, 10, 20)

def test_capture_recapture_ci_contains_estimate():
    est = capture_recapture(10, 10, 5)
    lo, hi = capture_recapture_ci(10, 10, 5)
    assert lo < est < hi

def test_saturation_curve():
    assert saturation_curve([1, 1, 2]) == [0.25, 0.5, 1.0]
```

- [ ] **Step 2: RED**: `uv run pytest -q` → 5 failures на старой формуле/отсутствующих функциях.

- [ ] **Step 3: Реализовать** Chapman `(n1+1)(n2+1)/(m+1)-1`, `inf` при `m=0`, валидацию входов, CI по асимптотической дисперсии, накопленную долю в `saturation_curve`.

- [ ] **Step 4: GREEN**: `uv run pytest -q`.

- [ ] **Step 5: Интеграция**: в `metrics.json` шаблона добавить `confirmed_count: 0` рядом с `findings`.

- [ ] **Step 6: Commit**: `git commit -m "fix: use Chapman estimator and expose completeness uncertainty"`

### Task 4: Исполняемое доказательство

**Files:**
- Create: `src/agentic_bioinformatics/evidence.py`, `tests/test_evidence.py`
- Modify: `src/agentic_bioinformatics/run.py`

**Interfaces:**
- Produces: `Evidence` dataclass (`evidence_class: str`, `artifact: Path`, `command: str`, `exit_code: int`); `require_confirmed(evidence: Evidence) -> None`; единый `_EVIDENCE` с добавленным `reference_match`

- [ ] **Step 1: Падающие тесты** в `tests/test_evidence.py`:
```python
from pathlib import Path
import pytest
from agentic_bioinformatics.evidence import Evidence, require_confirmed

def test_executed_test_evidence_passes(tmp_path):
    proof = tmp_path / "poc.txt"; proof.write_text("ok")
    require_confirmed(Evidence("reproducible_test", proof, "pytest -q", 0))

def test_missing_artifact_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        require_confirmed(Evidence("reproducible_poc", tmp_path/"no.py", "pytest -q", 0))

def test_failed_command_fails(tmp_path):
    proof = tmp_path / "poc.txt"; proof.write_text("ok")
    with pytest.raises(ValueError):
        require_confirmed(Evidence("reproducible_test", proof, "pytest -q", 1))

def test_missing_command_fails(tmp_path):
    proof = tmp_path / "poc.txt"; proof.write_text("ok")
    with pytest.raises(ValueError):
        require_confirmed(Evidence("reproducible_test", proof, "", 0))

def test_reference_match_accepted(tmp_path):
    proof = tmp_path / "results.csv"; proof.write_text("id,f1\n1,0.9")
    require_confirmed(Evidence("reference_match", proof, "grader.py", 0))
```

- [ ] **Step 2: RED**: `uv run pytest -q` → `ModuleNotFoundError: evidence`.

- [ ] **Step 3: Реализовать** `evidence.py`; в `run.py` импортировать `_EVIDENCE` оттуда и сохранить строковую обёртку `require_confirmed(evidence: str, artifact=None)` для совместимости со старыми тестами.

- [ ] **Step 4: GREEN**: `uv run pytest -q` (включая старые 14 тестов).

- [ ] **Step 5: Commit**: `git commit -m "feat: require executed proof for confirmed evidence"`

### Task 5: Схема трейса и валидация судьи

**Files:**
- Create: `src/agentic_bioinformatics/trace.py`, `src/agentic_bioinformatics/judge/validation.py`, `tests/test_trace.py`, `tests/test_judge_validation.py`
- Modify: `src/agentic_bioinformatics/judge/rubric.py`, `experiments/_template/run.py`

**Interfaces:**
- Produces: `TraceEvent` dataclass с полями `ts`, `event_id`, `agent_id`, `role`, `event`, `tool_call`, `tool_args`, `tool_result`, `tokens_in`, `tokens_out`, `parent_id` и методом `to_dict()`; `append_event(run_dir: Path, event: TraceEvent) -> None`; `cohen_kappa(a: list[int], b: list[int]) -> float`; `position_swap_agreement(a: list[int], b: list[int]) -> float`

- [ ] **Step 1: Падающие тесты**:
```python
# tests/test_trace.py
def test_trace_event_has_structured_fields():
    from agentic_bioinformatics.trace import TraceEvent
    e = TraceEvent(event="tool_call", agent_id="a1", role="executor",
                   tool_call="grep", tool_args={"q": "x"}, tokens_in=10, tokens_out=3)
    d = e.to_dict()
    assert d["event"] == "tool_call" and d["agent_id"] == "a1"
    assert {"ts", "event_id", "tokens_in", "tokens_out", "parent_id"} <= set(d)

def test_append_event_writes_jsonl(tmp_path):
    import json
    from agentic_bioinformatics.trace import TraceEvent, append_event
    append_event(tmp_path, TraceEvent(event="start"))
    append_event(tmp_path, TraceEvent(event="end"))
    lines = (tmp_path / "trace.jsonl").read_text().splitlines()
    assert len(lines) == 2 and json.loads(lines[1])["event"] == "end"

# tests/test_judge_validation.py
def test_cohen_kappa_perfect():
    from agentic_bioinformatics.judge.validation import cohen_kappa
    assert cohen_kappa([1, 1, 0, 0], [1, 1, 0, 0]) == 1.0

def test_cohen_kappa_known_value():
    from agentic_bioinformatics.judge.validation import cohen_kappa
    assert cohen_kappa([1, 1, 0, 0], [1, 0, 0, 0]) == 0.5

def test_position_swap_agreement():
    from agentic_bioinformatics.judge.validation import position_swap_agreement
    assert position_swap_agreement([1, 0, 1], [1, 0, 1]) == 1.0
```

- [ ] **Step 2: RED**: `uv run pytest -q` → `ModuleNotFoundError`.

- [ ] **Step 3: Реализовать** `TraceEvent` с `uuid4` и UTC-временем; `cohen_kappa = (po-pe)/(1-pe)`; position-swap как долю совпавших вердиктов.

- [ ] **Step 4: GREEN**: `uv run pytest -q`.

- [ ] **Step 5: Интеграция**: `rubric()` дополнить ключом `mast_categories` (3 категории MAST); шаблон пишет `TraceEvent` вместо плоского словаря.

- [ ] **Step 6: Commit**: `git commit -m "feat: structured traces and judge agreement validation"`

### Task 6: Финальная верификация, ревью и пуш

**Files:**
- Modify: `README.md`, `AGENTS.md` (описание новых конвенций)

- [ ] **Step 1: Обновить документацию** под новые поля и команды.

- [ ] **Step 2: Удалить устаревший прогон** `experiments/_template/runs/20261125T102726Z-42` после печати абсолютного пути и проверки.

- [ ] **Step 3: Полная проверка**: `make check`, `make sweep EXP=_template SEEDS=1,2,3`, `report.py`, `git status`.

- [ ] **Step 4: Commit и push**: `git commit -m "docs: describe reproducibility conventions"`, `git push origin main`, проверить `origin/main == HEAD`.

- [ ] **Step 5: Независимое ревью** subagent на hy4 flash по полному диапазону коммитов; Critical/Important — один fix pass с RED→GREEN.

- [ ] **Step 6: Итог**: сообщить пользователю результаты проверок и список оставшихся SHOULD/NICE.

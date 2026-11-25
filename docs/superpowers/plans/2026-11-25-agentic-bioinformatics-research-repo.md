# Agentic Bioinformatics Research Repo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpower-subagent-driven-development (recommended) or superpower-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Создать чистый, воспроизводимый локальный git-репозиторий с изолированным Python-окружением и минимальным каркасом для экспериментов по оркестрации LLM-агентов в биоинформатике.

**Architecture:** Используем санкционированный `newproj` для uv-проекта ( `.venv`, `uv.lock`, `.gitignore`, `README.md`, `AGENTS.md`, git, приватный GitHub). Поверх него — каталоги `src/abio`, `experiments`, `data`, `docs`, `tests` и минимальное ядро воспроизводимости: артефакты прогона, классы доказательств, метрики полноты. Харнес подключается адаптером, а не жёсткой зависимостью.

**Tech Stack:** bash, git, uv, Python 3.13, pytest, ruff, PyYAML, gh CLI.

**Spec:** `docs/superpowers/specs/2026-11-25-agentic-bioinformatics-research-repo-design.md`

## Global Constraints

- Python 3.13 из miniforge; `.venv` только внутри проекта; глобальный `pip install` в base запрещён.
- Зависимости только через `uv add` / `uv sync`; `uv.lock` обязательно коммитится.
- Целевой путь: `/Users/vitalypesnev/Projects/research/agentic-bioinformatics`.
- Старая пустая папка `/Users/vitalypesnev/Projects/research/agentic bioinformatics` удаляется только после печати абсолютного пути и проверки пустоты.
- GitHub: приватный репозиторий; `newproj` создаёт его сам при наличии `gh auth`; при отсутствии — локальный git остаётся рабочим, ретраи не бесконечные.
- Секреты только в `.env` (в `.gitignore`); `.env.example` — заглушки.
- Conda-env `rvk`, `rvk_analysis` и `~/miniforge3` не трогать.

## Review Focus

- `gh` не авторизован → репозиторий всё равно создаётся локально, GitHub честно пропускается без падения (Task 2).
- `.env` с реальным ключом не должен попасть в индекс git (Task 4: `git check-ignore`).
- `capture_recapture` при `m = 0` не должен делить на ноль (Task 5).
- Статус «подтверждено» без исполняемого доказательства не должен проходить (Task 5).
- `.uv-cache` / `.venv` не должны коммититься (Task 2 и Task 4: `git check-ignore`).

---

### Task 1: Preflight и удаление пустой папки

**Files:**
- Remove: `/Users/vitalypesnev/Projects/research/agentic bioinformatics` (пустой каталог)

**Interfaces:**
- Consumes: ничего
- Produces: свободная рабочая папка без каталога с пробелом; подтверждённые `uv`, `gh`, отсутствие целевого пути

- [ ] **Step 1: Напечатать абсолютные пути и проверить пустоту**

Run:
```bash
echo "$PWD/agentic bioinformatics"
ls -la "$PWD/agentic bioinformatics"
```
Expected: путь напечатан, вывод `ls` показывает только `.` и `..`.

- [ ] **Step 2: Проверить инструменты и отсутствие цели**

Run:
```bash
command -v uv; command -v gh || echo "gh отсутствует"
gh auth status >/dev/null 2>&1 && echo "gh: авторизован" || echo "gh: НЕ авторизован"
python3 --version
[ ! -e "$PWD/agentic-bioinformatics" ] && echo "цель свободна"
```
Expected: `uv` найден; `python3` → 3.13.x; «цель свободна».

- [ ] **Step 3: Удалить пустую папку**

Run:
```bash
rmdir "$PWD/agentic bioinformatics"
```
Expected: код 0, `ls -d "agentic bioinformatics"` → No such file or directory.

- [ ] **Step 4: Подтвердить чистое состояние**

Run: `ls -la "$PWD"`
Expected: осталась только папка `docs/` со spec и планом.

- [ ] **Step 5: Commit**

Нет git-репозитория — коммит выполняется в Task 2.

### Task 2: Scaffold через newproj

**Files:**
- Create (generates): `pyproject.toml`, `uv.lock`, `.python-version`, `main.py`, `README.md`, `AGENTS.md`, `.gitignore`, `.venv/`, `.git/`

**Interfaces:**
- Consumes: свободный целевой путь из Task 1
- Produces: рабочий uv-проект с первым коммитом; опционально `origin`

- [ ] **Step 1: Создать проект**

Run:
```bash
newproj agentic-bioinformatics --root /Users/vitalypesnev/Projects/research
```
Expected: код 0, в конце «Готово: .../agentic-bioinformatics».

- [ ] **Step 2: Проверить артефакты scaffold**

Run:
```bash
cd /Users/vitalypesnev/Projects/research/agentic-bioinformatics
ls -la
.venv/bin/python --version
git log --oneline -1
test -f uv.lock && echo "lock есть"
```
Expected: все файлы на месте; Python 3.13.x; один коммит `chore: bootstrap agentic-bioinformatics`.

- [ ] **Step 3: Зафиксировать состояние GitHub и ignore-правил**

Run:
```bash
git remote -v | head -2 || true
git check-ignore -v .venv
git status --short
```
Expected: `git status` чист; `.venv` проигнорирован; `origin` есть если `gh` авторизован, иначе — честно отсутствует (не считать ошибкой).

- [ ] **Step 4: Commit**

`newproj` уже создал bootstrap-коммит; дополнительный коммит не требуется.

### Task 3: Перенос spec/плана в репозиторий и dev-инструменты

**Files:**
- Create: `docs/superpowers/specs/2026-11-25-agentic-bioinformatics-research-repo-design.md`, `docs/superpowers/plans/2026-11-25-agentic-bioinformatics-research-repo.md`
- Modify: `pyproject.toml`, `uv.lock`

**Interfaces:**
- Consumes: проект из Task 2
- Produces: spec и план внутри репозитория; `ruff`, `pytest`, `pyyaml` в dev-зависимостях

- [ ] **Step 1: Скопировать документы**

Run:
```bash
cd /Users/vitalypesnev/Projects/research/agentic-bioinformatics
mkdir -p docs/superpowers/specs docs/superpowers/plans
cp ../docs/superpowers/specs/2026-11-25-agentic-bioinformatics-research-repo-design.md docs/superpowers/specs/
cp ../docs/superpowers/plans/2026-11-25-agentic-bioinformatics-research-repo.md docs/superpowers/plans/
```
Expected: оба файла существуют в репозитории.

- [ ] **Step 2: Добавить dev-зависимости**

Run:
```bash
uv add --dev ruff pytest pyyaml
```
Expected: `pyproject.toml` и `uv.lock` обновлены.

- [ ] **Step 3: Проверить инструменты**

Run:
```bash
uv run ruff check . && uv run pytest -q
```
Expected: ruff проходит; pytest показывает `no tests ran` (это ок на этом этапе).

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "docs: add spec and plan, configure dev tooling"
```

### Task 4: Структура каталогов, AGENTS.md, README, Makefile

**Files:**
- Create: `src/abio/.gitkeep`, `src/abio/metrics/.gitkeep`, `src/abio/judge/.gitkeep`, `src/abio/harness/.gitkeep`, `experiments/.gitkeep`, `data/raw/.gitkeep`, `data/reference/.gitkeep`, `data/canaries/.gitkeep`, `docs/literature/.gitkeep`, `notebooks/.gitkeep`, `tests/.gitkeep`, `.env.example`, `Makefile`
- Modify: `AGENTS.md`, `README.md`, `.gitignore`

**Interfaces:**
- Consumes: docs и инструменты из Task 3
- Produces: стандартная раскладка репозитория; команды `make check`, `make run EXP=...`

- [ ] **Step 1: Создать структуру**

Run:
```bash
mkdir -p src/abio/metrics src/abio/judge src/abio/harness experiments \
  data/raw data/reference data/canaries docs/literature notebooks tests
touch src/abio/.gitkeep src/abio/metrics/.gitkeep src/abio/judge/.gitkeep \
  src/abio/harness/.gitkeep experiments/.gitkeep data/raw/.gitkeep \
  data/reference/.gitkeep data/canaries/.gitkeep docs/literature/.gitkeep \
  notebooks/.gitkeep tests/.gitkeep
```
Expected: `find . -type d -not -path './.git*' -not -path './.venv*'` показывает нужные каталоги.

- [ ] **Step 2: Написать `.env.example` и дополнить `.gitignore`**

`.env.example` содержит только заглушки, например:
```
DEEPSEEK_API_KEY=
OPENAI_API_KEY=
```
В `.gitignore` добавить строки:
```
.uv-cache/
runs/
data/raw/*
!data/raw/.gitkeep
```
Expected: `git check-ignore -v .env` и `git check-ignore -v .uv-cache` оба дают совпадение.

- [ ] **Step 3: Дополнить `AGENTS.md`**

Добавить разделы «Структура», «Эксперименты», «Правила доказательств», «Куда класть spec/plan».

Expected: `grep -c 'Правила доказательств' AGENTS.md` даёт 1.

- [ ] **Step 4: Переписать `README.md`**

Назначение проекта, `uv sync`, `make check`, `make run EXP=<name>`, ссылки на spec и план.

Expected: в README есть команда воспроизведения одной строкой.

- [ ] **Step 5: Создать `Makefile`**

Цели:
- `check`: `uv run ruff check . && uv run pytest -q`
- `run EXP=`: `uv run python experiments/$(EXP)/run.py`

Expected: `make -n check` печатает команды без выполнения.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "chore: add repo structure, docs and make targets"
```

### Task 5: Минимальное ядро воспроизводимости (TDD)

**Files:**
- Create: `src/abio/__init__.py`, `src/abio/run.py`, `src/abio/metrics/__init__.py`, `src/abio/metrics/coverage.py`, `src/abio/metrics/canaries.py`, `src/abio/judge/__init__.py`, `src/abio/judge/rubric.py`, `src/abio/harness/__init__.py`
- Test: `tests/test_run.py`, `tests/test_coverage.py`, `tests/test_canaries.py`, `tests/test_rubric.py`, `tests/test_harness.py`

**Interfaces:**
- Consumes: структура и dev-зависимости из Task 3–4
- Produces:
  - `new_run(exp: str, seed: int, base: Path = Path("experiments")) -> Path` — каталог `runs/<timestamp>-<seed>/`
  - `write_config(run_dir: Path, config: dict) -> None` — `config.yaml`
  - `append_trace(run_dir: Path, event: dict) -> None` — `trace.jsonl`
  - `write_metrics(run_dir: Path, metrics: dict) -> None` — `metrics.json`
  - `EVIDENCE_CLASSES: tuple[str, ...]` — `("hypothesis", "code_reference", "static_analyzer", "reproducible_poc", "sanitizer_crash")`
  - `require_confirmed(evidence: str) -> None` — бросает `ValueError` для классов ниже `reproducible_poc`
  - `capture_recapture(n1: int, n2: int, m: int) -> float` — оценка `n1*n2/m`, `0.0` при `m == 0`
  - `coverage_matrix(cells: list[tuple[str, str]], covered: set[tuple[str, str]]) -> dict`
  - `canary_recall(injected: dict[str, int], caught: dict[str, int]) -> dict[str, float]`
  - `rubric() -> dict` — словарь критериев судьи
  - `HarnessAdapter` — `typing.Protocol` с методом `run(config: dict) -> dict`; адаптеры харнесов реализуют его

- [ ] **Step 1: Написать падающие тесты**

`tests/test_run.py`:
```python
def test_new_run_creates_timestamp_seed_dir(tmp_path):
    d = new_run("debate_vs_sampling", 42, base=tmp_path)
    assert d.exists() and "42" in d.name

def test_run_artifacts(tmp_path):
    d = new_run("e", 1, base=tmp_path)
    write_config(d, {"model": "deepseek"})
    append_trace(d, {"event": "start"})
    write_metrics(d, {"precision": 0.8})
    assert (d / "config.yaml").exists()
    assert (d / "trace.jsonl").read_text().count("\n") == 1
    assert (d / "metrics.json").exists()

def test_confirmed_requires_proof():
    import pytest
    with pytest.raises(ValueError):
        require_confirmed("hypothesis")
    require_confirmed("reproducible_poc")
```

`tests/test_coverage.py`:
```python
def test_capture_recapture_zero_intersection():
    assert capture_recapture(10, 8, 0) == 0.0

def test_capture_recapture_estimate():
    assert capture_recapture(10, 10, 5) == 20.0

def test_coverage_matrix_marks_uncovered():
    cells = [("api", "CWE-79"), ("cli", "CWE-78")]
    result = coverage_matrix(cells, {("api", "CWE-79")})
    assert result["covered"] == 1 and result["uncovered"] == 1
```

`tests/test_canaries.py`:
```python
def test_canary_recall_per_class():
    result = canary_recall({"CWE-79": 10, "CWE-78": 5}, {"CWE-79": 8, "CWE-78": 1})
    assert result == {"CWE-79": 0.8, "CWE-78": 0.2}
```

`tests/test_rubric.py`:
```python
def test_rubric_has_required_keys():
    r = rubric()
    assert {"evidence", "coverage", "novelty"} <= set(r)
```

`tests/test_harness.py`:
```python
def test_dummy_adapter_satisfies_protocol():
    class Dummy:
        def run(self, config: dict) -> dict:
            return config

    assert isinstance(Dummy(), HarnessAdapter)
```

- [ ] **Step 2: Показать, что тесты падают**

Run: `uv run pytest -q`
Expected: FAIL с `ImportError` / `[Errno 2]` — модули ещё не созданы.

- [ ] **Step 3: Реализовать minimal API**

Реализовать функции ровно с сигнатурами из Interfaces. `new_run` использует `datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")`. `require_confirmed` допускает только `reproducible_poc` и `sanitizer_crash`. `coverage_matrix` возвращает `{"total": ..., "covered": ..., "uncovered": ..., "uncovered_cells": [...]}`. `canary_recall` делит `caught` на `injected`, классы без инъекций пропускает. `HarnessAdapter` — `Protocol` с `@runtime_checkable`.

- [ ] **Step 4: Прогнать тесты**

Run: `uv run pytest -q`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: add reproducibility core with tests"
```

### Task 6: Финальная верификация и шаблон эксперимента

**Files:**
- Create: `experiments/_template/config.yaml`, `experiments/_template/run.py`

**Interfaces:**
- Consumes: ядро из Task 5
- Produces: работающий шаблон прогона; подтверждённая воспроизводимость

- [ ] **Step 1: Создать шаблон эксперимента**

`config.yaml`:
```yaml
name: template
model: deepseek
seed: 42
budget_tokens: 10000
```
`run.py`: читает конфиг через `yaml.safe_load`, вызывает `new_run`, `write_config`, `append_trace`, `write_metrics`, печатает путь к прогону.

- [ ] **Step 2: Запустить шаблон**

Run: `make run EXP=_template`
Expected: напечатан путь вида `experiments/_template/runs/<timestamp>-42/`, внутри `config.yaml`, `trace.jsonl`, `metrics.json`.

- [ ] **Step 3: Прогнать все проверки**

Run: `make check`
Expected: `ruff check` проходит, `pytest -q` → все тесты зелёные.

- [ ] **Step 4: Проверить чистоту репозитория и remote**

Run:
```bash
git status --short
git remote -v
git check-ignore -v .env .venv .uv-cache
```
Expected: рабочее дерево чисто (кроме проигнорированных артефактов прогона); `origin` есть при авторизованном `gh`; ignore-правила срабатывают.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: add experiment template and verify reproducibility"
```

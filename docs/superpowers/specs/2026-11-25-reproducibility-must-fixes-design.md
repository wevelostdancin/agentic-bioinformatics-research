# Дизайн: MUST-исправления воспроизводимости (по итогам литературного ревью)

Дата: 2026-11-25
Статус: ожидает ревью

## 1. Контекст

Тиммейт на hy4 flash сравнил репозиторий с MAST, BixBench, BioAgent Bench, AIxCC,
MoA/More Agents, Wohlin 1995, Comcast 2026, Zheng et al. и AFlow. Вердикт: каркас верный,
но воспроизводимость пока декларативная. Пользователь утвердил список MUST-правок.

Текущее состояние проверено локально: `seed` используется только в имени каталога;
`trace.jsonl` содержит одно событие; файлы в `data/*` и `docs/literature/` отсутствуют;
в старом прогоне нет новых полей конфига.

## 2. Цели (пять MUST)

1. **Seed реально применяется**, вариативность измеряется, учитываются фактические токены.
2. **Provenance-снапшот и валидатор артефактов**: каждый прогон самодостаточен.
3. **Корректная оценка полноты**: смещённая оценка заменена, неопределённость явная.
4. **Исполняемое доказательство**: гейт проверяет не метку и не «файл есть», а результат исполнения.
5. **Схема трейса и валидация судьи**: события пригодны для MAST-разметки, судья проверяется согласием.

## 3. Ограничения

- Изменения только внутри репозитория; внешние действия — коммиты и пуш в приватный GitHub.
- TDD: каждый новый поведение сначала падающий тест, затем минимальный код.
- Совместимость: существующие 14 тестов должны остаться зелёными (или быть явно переписаны с рулингом).
- Никаких тяжёлых зависимостей: stdlib + уже установленные pytest/ruff/pyyaml.
- Контракт машины: `UV_CACHE_DIR` в рабочей папке, `.venv` проекта, `make check` перед «готово».

## 4. Дизайн по пунктам

### 4.1 Seed, вариативность, токены

Новый модуль `src/agentic_bioinformatics/repro.py`:
- `set_seed(seed: int) -> None` — детерминирует `random`; вызывается шаблоном до всех действий.
- `aggregate(values: list[float]) -> dict` — `mean`, `std`, `n`, `ci_low`, `ci_high` (нормальное приближение 1.96·SE); при `n < 2` CI = `None`.
- `TokenCounter` — dataclass с полями `in_tokens`, `out_tokens`, метод `add()`, `as_dict()`.

Шаблон: вызывает `set_seed`, пишет `tokens_used` и `repetition` в `metrics.json`.
Новая цель `make sweep EXP=... SEEDS=1,2,3` — прогон шаблона с разными сидами и агрегация.

### 4.2 Provenance и валидатор

Новый модуль `src/agentic_bioinformatics/provenance.py`:
- `snapshot(repo_root: Path, config: dict) -> dict` — `git_sha` (`git -C ... rev-parse HEAD`),
  `uv_lock_sha256`, `data_sha256` (по файлам `data/`, кроме `.gitkeep`), `prompt_version`
  и `tool_versions` из конфига.
- `validate_run(run_dir: Path) -> list[str]` — проверяет наличие 4 артефактов и обязательных
  полей (`model_version`, `harness_version`, `seed`, `git_sha`, `uv_lock_sha256`);
  возвращает список проблем. `require_valid_run` бросает `ValueError` при проблемах.
- Шаблон вызывает `snapshot` и записывает результат в `config.yaml`; `make check`
  остаётся прежним, валидатор вызывается в smoke-прогоне.

### 4.3 Корректная полнота

`metrics/coverage.py`:
- `capture_recapture(n1, n2, m) -> float` — оценка Chapmanа `(n1+1)(n2+1)/(m+1)-1`;
  при `m == 0` → `float("inf")` (оценка не определена, не ноль);
  валидация `n1,n2 >= 0`, `0 <= m <= min(n1,n2)`.
- `capture_recapture_ci(n1, n2, m) -> tuple[float, float]` — доверительный интервал.
- `saturation_curve(counts: list[int]) -> list[float]` — накопленная доля новых находок.
- `coverage_matrix` остаётся, отчёт явно содержит `uncovered_cells`.
- В метриках шаблона разделяем `findings` и `confirmed_count`.

### 4.4 Исполняемое доказательство

`src/agentic_bioinformatics/evidence.py`:
- `Evidence` dataclass: `evidence_class`, `artifact: Path`, `command: str`, `exit_code: int`.
- `require_confirmed(evidence: Evidence) -> None` допускает только исполняемые классы из
  единого `_EVIDENCE`, требует `artifact.is_file()`, непустую `command` и `exit_code == 0`.
- Добавляем класс `reference_match` (для био-задач с ground truth/F1, где бинарного PoC нет).
- `run.py` сохраняет обратную совместимость: строковый вызов по-прежнему отклоняет слабые
  классы и проверяет существование артефакта, но статус «подтверждено» требует `Evidence`.

### 4.5 Трейс и судья

- `src/agentic_bioinformatics/trace.py`: `TraceEvent` dataclass (`ts`, `event_id`, `agent_id`,
  `role`, `event`, `tool_call`, `tool_args`, `tool_result`, `tokens_in`, `tokens_out`,
  `parent_id`) + `append_event()`; старый `append_trace(dict)` остаётся.
- `src/agentic_bioinformatics/judge/validation.py`: `cohen_kappa(a, b) -> float`,
  `position_swap_agreement(a, b) -> float`; rubric дополняется категориями MAST.
- Шаблон пишет `TraceEvent` вместо плоского словаря.

## 5. Вне объёма

Выбор конкретного бенчмарка и наполнение данными, реальные агенты и LLM-вызовы, реализация
LangGraph/BioinfoMCP адаптеров, автопоиск оркестрации (ADAS/AFlow).

## 6. Верификация

- `make check` зелёный; число тестов вырастает с 14 минимум до 22.
- Smoke: `make sweep EXP=_template SEEDS=1,2,3` создаёт три прогона, валидатор проходит,
  в метриках есть `tokens_used`, `repetition`, `mean/std/CI`.
- `git status` чист после коммитов; `origin/main == HEAD`.

## 7. Риски

| Риск | Мера |
|---|---|
| Перелом существующих тестов | Явно переписать ожидания Chapmanа в тестах, зафиксировать рулинг |
| Усложнение API | Держать старые функции как совместимые обёртки |
| Отсутствие реального LLM-вызова | Seed и токены проверяем на детерминизме RNG и счётчике, не на модели |

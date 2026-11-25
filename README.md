# agentic-bioinformatics

Локальный репозиторий для исследований LLM-based multi-agent systems в биоинформатике:
оркестрация агентов, верификация находок и оценка полноты покрытия.

## Воспроизведение

    uv sync
    make check

## Эксперимент

    make run EXP=<name>
    make sweep EXP=<name> SEEDS=1,2,3

Каждый прогон фиксирует конфиг (версии модели и харнеса, git SHA, хэш `uv.lock`, хэши данных), сид, структурированный трейс, метрики и `summary.md` в `experiments/<name>/runs/`. `sweep` делает 3–5 повторов с разными сидами; `uv run python experiments/_template/report.py` печатает mean ± CI.

## Воспроизводимость

- `set_seed()` реально детерминирует RNG; сид пишется в конфиг и имя прогона.
- Полнота считается оценкой Chapmanа с доверительным интервалом; `m=0` означает «оценка не определена», а не ноль.
- Подтверждение требует `Evidence`: исполняемая команда, exit code 0 и существующий proof-файл. Для био-задач есть класс `reference_match`.
- Валидатор (`require_valid_run`) проверяет 4 артефакта и обязательные поля конфига.
- Судья проверяется согласием: `cohen_kappa` и `position_swap_agreement`.

## Структура

- `src/agentic_bioinformatics/` — переиспользуемый код (артефакты прогона, метрики, rubric, адаптеры харнесов).
- `experiments/` — по папке на дизайн исследования.
- `data/raw`, `data/reference`, `data/canaries` — данные, известная правда и канарейки.
- `docs/superpowers` — spec и план; `docs/literature` — карта литературы.
- `tests/` — проверки ядра воспроизводимости.

## Документы

- [Spec: дизайн репозитория](docs/superpowers/specs/2026-11-25-agentic-bioinformatics-research-repo-design.md) — исторический
- [Plan: исходный план](docs/superpowers/plans/2026-11-25-agentic-bioinformatics-research-repo.md) — исторический
- [Spec: MUST-исправления](docs/superpowers/specs/2026-11-25-reproducibility-must-fixes-design.md) — актуальный
- [Plan: MUST-исправления](docs/superpowers/plans/2026-11-25-reproducibility-must-fixes.md) — актуальный

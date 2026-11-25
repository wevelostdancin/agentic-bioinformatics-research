# agentic-bioinformatics

Локальный репозиторий для исследований LLM-based multi-agent systems в биоинформатике:
оркестрация агентов, верификация находок и оценка полноты покрытия.

## Воспроизведение

    uv sync
    make check

## Эксперимент

    make run EXP=<name>

Каждый прогон фиксирует конфиг (включая версии модели и харнеса), сид, трейс, метрики и краткий отчёт `summary.md` в `experiments/<name>/runs/`.

## Структура

- `src/agentic_bioinformatics/` — переиспользуемый код (артефакты прогона, метрики, rubric, адаптеры харнесов).
- `experiments/` — по папке на дизайн исследования.
- `data/raw`, `data/reference`, `data/canaries` — данные, известная правда и канарейки.
- `docs/superpowers` — spec и план; `docs/literature` — карта литературы.
- `tests/` — проверки ядра воспроизводимости.

## Документы

- [Spec: дизайн репозитория](docs/superpowers/specs/2026-11-25-agentic-bioinformatics-research-repo-design.md)
- [Plan: план выполнения](docs/superpowers/plans/2026-11-25-agentic-bioinformatics-research-repo.md)

# AGENTS.md — agentic-bioinformatics

## Окружение
- Python: uv + .python-version, venv в .venv. Глобальный pip install запрещён.
- Зависимости: uv add <pkg> (обновляет pyproject.toml и uv.lock).
- Воспроизведение: `uv sync`. Замеры запускать через `.venv/bin/python`.

## Проверки перед «готово»

    make check

## Структура
- `src/agentic_bioinformatics/` — переиспользуемый код: `run.py`, `metrics/`, `judge/`, `harness/`.
- `experiments/<name>/` — один дизайн: `config.yaml`, `run.py`, `runs/`.
- `data/raw/` — иммутабельные исходные данные; `data/reference/` — известная правда; `data/canaries/` — инжектированные известные дефекты.
- `docs/superpowers/` — spec и планы; `docs/literature/` — карта литературы.
- `notebooks/` — разведка, не источник правды; `tests/` — проверки.

## Эксперименты
- Запуск: `make run EXP=<name>`. Каждый прогон пишет `config.yaml`, `trace.jsonl`, `metrics.json` в `experiments/<name>/runs/<timestamp>-<seed>/`.
- Один меняющийся фактор за раз, равный токен-бюджет, минимум 3–5 повторов с разными сидами, байслайн «один агент» перед оркестрацией.

## Правила доказательств
- «Подтверждено» — только исполняемое доказательство: PoC, воспроизводимый тест, крэш под санитайзером, опора на ground truth.
- «Опровергнуто» — только контр-доказательство, а не мнение LLM-судьи.
- Полнота — оценка остатка и явные непокрытые зоны, а не гарантия.

## Куда класть spec/plan
- `docs/superpowers/specs/YYYY-MM-DD-*-design.md`
- `docs/superpowers/plans/YYYY-MM-DD-*.md`

## Правила
- Lock-файл (uv.lock) коммитится — окружение воспроизводимо.
- Секреты — только в .env (он в .gitignore), `.env.example` содержит заглушки.

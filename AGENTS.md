# AGENTS.md — agentic-bioinformatics

## Окружение
- Python: uv + .python-version, venv в .venv. Глобальный pip install запрещён.
- Зависимости: uv add <pkg> (обновляет pyproject.toml и uv.lock).

## Проверки перед «готово»

    uv run ruff check .
    uv run pytest -q

## Правила
- Lock-файл (uv.lock) коммитится — окружение воспроизводимо.
- Секреты — только в .env (он в .gitignore).

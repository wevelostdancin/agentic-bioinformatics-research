.PHONY: check run

check:
	uv run ruff check . && uv run pytest -q

run:
	uv run python experiments/$(EXP)/run.py

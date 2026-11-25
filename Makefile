.PHONY: check run sweep bootstrap

comma := ,

bootstrap:
	bash scripts/bootstrap.sh

check:
	uv run ruff check . && uv run pytest -q

run:
	uv run python experiments/$(EXP)/run.py

sweep:
	@for s in $(subst $(comma), ,$(SEEDS)); do SEED=$$s $(MAKE) run EXP=$(EXP); done

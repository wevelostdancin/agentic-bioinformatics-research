#!/usr/bin/env bash
# One-command setup on a fresh machine.
set -euo pipefail

cd "$(dirname "$0")/.."
export UV_CACHE_DIR="${UV_CACHE_DIR:-$PWD/.uv-cache}"

echo "==> Installing the pinned environment"
uv sync --frozen

if [ ! -f .env ]; then
  cp .env.example .env
  echo "==> Created .env from .env.example — fill in your API keys before real experiments"
else
  echo "==> .env already present, keeping it"
fi

echo "==> Checking lint and tests"
make check

echo "==> Smoke run"
make run EXP=_template

echo "==> Bootstrap complete. Next: read docs/ENVIRONMENT.md and data/manifest.yaml"

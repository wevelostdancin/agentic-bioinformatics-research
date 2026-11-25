#!/usr/bin/env bash
# Print SHA256 hashes of local benchmark data; copy the results into data/manifest.yaml.
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON=".venv/bin/python"
[ -x "$PYTHON" ] || PYTHON="python3"

"$PYTHON" - <<'PY'
import hashlib
from pathlib import Path

roots = [Path("data") / name for name in ("raw", "reference", "canaries")]
paths = sorted(
    p for root in roots if root.is_dir()
    for p in root.rglob("*") if p.is_file() and p.name != ".gitkeep"
)
if not paths:
    print("No data files found. See data/manifest.yaml for the download command.")
for path in paths:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"{digest}  {path}")
PY

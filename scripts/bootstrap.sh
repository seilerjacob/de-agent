#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Bootstrapping DE Agent pipeline..."

if [ ! -d "$ROOT/.venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv "$ROOT/.venv"
fi

echo "  Installing dependencies..."
"$ROOT/.venv/bin/pip" install --quiet -r "$ROOT/requirements.txt"

if [ -f "$ROOT/requirements-dev.txt" ]; then
    "$ROOT/.venv/bin/pip" install --quiet -r "$ROOT/requirements-dev.txt"
fi

echo "  Done. Activate with: source .venv/bin/activate"

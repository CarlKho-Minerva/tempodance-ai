#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$project_dir"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

if [[ -x ".venv/bin/python" ]]; then
  tempo_python=".venv/bin/python"
elif [[ -x "venv/bin/python" ]]; then
  tempo_python="venv/bin/python"
else
  tempo_python="python3"
fi

exec "$tempo_python" -m uvicorn backend.main:app --host 127.0.0.1 --port "${PORT:-8000}" "$@"

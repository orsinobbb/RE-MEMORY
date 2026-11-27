#!/bin/sh
set -eu
cd "$(dirname "$0")"
if ! command -v uv >/dev/null 2>&1; then
  printf '%s\n' 'Please install uv from https://docs.astral.sh/uv/getting-started/installation/ and rerun this script.'
  exit 1
fi
uv sync --frozen --python 3.12
if [ ! -f .env ]; then cp .env.example .env; chmod 600 .env; fi
APP_LOCAL_PORT=$(uv run --no-sync python -c "from dotenv import dotenv_values; print(dotenv_values('.env').get('APP_PORT') or '8791')")
printf 'RE:MEMORY Local URL: http://127.0.0.1:%s\n' "$APP_LOCAL_PORT"
exec uv run --no-sync python -m uvicorn app.main:app --host 127.0.0.1 --port "$APP_LOCAL_PORT"

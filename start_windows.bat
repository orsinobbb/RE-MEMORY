@echo off
setlocal
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 (
  echo Install uv from https://docs.astral.sh/uv/getting-started/installation/ and rerun.
  exit /b 1
)
uv sync --frozen --python 3.12
if errorlevel 1 exit /b 1
if not exist .env copy .env.example .env >nul
for /f "delims=" %%p in ('uv run --no-sync python -c "from dotenv import dotenv_values; print(dotenv_values('.env').get('APP_PORT') or '8791')"') do set "REMEMORY_PORT=%%p"
echo RE:MEMORY Local URL: http://127.0.0.1:%REMEMORY_PORT%
uv run --no-sync python -m uvicorn app.main:app --host 127.0.0.1 --port %REMEMORY_PORT%

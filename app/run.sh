#!/usr/bin/env bash
# Build the UI if needed, then serve UI + API at http://localhost:8765
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d web/node_modules ]; then (cd web && npm install); fi
if [ ! -f web/dist/index.html ] || [ -n "$(find web/src -newer web/dist/index.html -print -quit)" ]; then (cd web && npm run build); fi
cd ..
exec uv run --with fastapi --with uvicorn uvicorn app.server:app --port "${PORT:-8765}"

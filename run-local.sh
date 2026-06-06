#!/usr/bin/env bash
# Arrenca el Generador d'Acudits en LOCAL per provar-lo al navegador.
#
#   ./run-local.sh
#
# Detecta el binari de Claude de l'extensió de VS Code (o el 'claude' del PATH),
# crea l'entorn virtual si cal, instal·la dependències i engega el servidor a
# http://localhost:8200
set -euo pipefail
cd "$(dirname "$0")"

# ─── Localitza el CLI de Claude ─────────────────────────────
if command -v claude >/dev/null 2>&1; then
  export CLAUDE_CMD="claude"
else
  # Binari natiu que porta l'extensió de VS Code (agafa la versió més nova)
  CAND=$(ls -d "$HOME"/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude 2>/dev/null | sort -V | tail -1 || true)
  if [ -n "${CAND:-}" ] && [ -x "$CAND" ]; then
    export CLAUDE_CMD="$CAND"
  else
    echo "⚠️  No s'ha trobat el CLI 'claude'. Instal·la Claude Code o l'extensió de VS Code." >&2
    exit 1
  fi
fi
echo "Claude: $CLAUDE_CMD"

# ─── Entorn de Python ───────────────────────────────────────
if [ ! -d .venv ]; then
  echo "Creant entorn virtual…"
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt

# ─── Engega el servidor ─────────────────────────────────────
export DATA_DIR="./data"
echo "Obre http://localhost:8200"
exec .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8200 --reload

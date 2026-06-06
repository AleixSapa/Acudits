"""Configuració global llegida de l'entorn (variables d'entorn / .env de Dokploy)."""
from __future__ import annotations

import os
from pathlib import Path

# Arrel del projecte (la carpeta que conté backend/, frontend/, data/)
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Servidor ───────────────────────────────────────────────
PORT = int(os.getenv("PORT", "8200"))

# ─── Motor d'IA (Claude Code, ja instal·lat i autenticat al contenidor) ──
# Ordre per invocar el CLI. El prompt s'hi passa per STDIN.
CLAUDE_CMD = os.getenv("CLAUDE_CMD", "claude")
# Model a fer servir (buit = el per defecte del CLI). 'opus' fa acudits més enginyosos
# i originals (per defecte); 'sonnet' és més ràpid però amb humor més tòpic.
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "opus").strip()
# Temps màxim (segons) per a una generació (opus pot trigar més)
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "180"))

# Quants acudits ja existents s'envien a Claude com a context perquè NO els repeteixi.
# Es limita per no fer el prompt massa llarg quan la base de dades creixi molt.
MAX_CONTEXT_JOKES = int(os.getenv("MAX_CONTEXT_JOKES", "300"))

# ─── Rutes de dades ─────────────────────────────────────────
def _path(env_name: str, default: str) -> Path:
    raw = os.getenv(env_name, default)
    p = Path(raw)
    if not p.is_absolute():
        p = (BASE_DIR / p).resolve()
    return p


# Carpeta de dades persistents (en producció és un volum de Dokploy muntat a /app/data)
DATA_DIR = _path("DATA_DIR", "./data")
DB_PATH = DATA_DIR / "acudits.db"

# Carpeta del frontend estàtic
FRONTEND_DIR = BASE_DIR / "frontend"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

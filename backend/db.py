"""Capa fina d'accés a SQLite per als acudits.

Cada acudit es desa amb una versió NORMALITZADA del text (columna `norm`, UNIQUE),
que serveix per detectar duplicats encara que canviïn majúscules, accents o
espais. Així, en generar-ne un de nou, sabem si ja existeix o no.
"""
from __future__ import annotations

import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from typing import Optional

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS acudits (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    text       TEXT NOT NULL,            -- l'acudit tal com es mostra
    norm       TEXT UNIQUE NOT NULL,     -- versió normalitzada per detectar duplicats
    created_at TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(text: str) -> str:
    """Normalitza un acudit per comparar duplicats: minúscules, sense accents,
    sense signes de puntuació i amb els espais col·lapsats."""
    text = text.lower().strip()
    # Treu accents (à→a, ç→c, ñ→n...)
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    # Deixa només lletres i números separats per un sol espai
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_conn() -> sqlite3.Connection:
    config.ensure_dirs()
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    # Garanteix l'esquema a cada connexió: si el fitxer de BD s'esborra o encara no
    # existeix, l'app es recupera sola en comptes de fallar amb "no such table".
    conn.executescript(SCHEMA)
    return conn


def init_db() -> None:
    config.ensure_dirs()
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def add_acudit(text: str) -> tuple[Optional[sqlite3.Row], bool]:
    """Afegeix un acudit si encara no existeix.

    Retorna (fila, es_nou):
      - Si és nou: (la fila creada, True)
      - Si ja existia: (la fila existent, False)  → no s'afegeix res.
    """
    text = (text or "").strip()
    norm = normalize(text)
    if not norm:
        return None, False
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT * FROM acudits WHERE norm = ?", (norm,)
        ).fetchone()
        if existing is not None:
            return existing, False
        cur = conn.execute(
            "INSERT INTO acudits (text, norm, created_at) VALUES (?, ?, ?)",
            (text, norm, now_iso()),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM acudits WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return row, True


def list_acudits() -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM acudits ORDER BY created_at DESC"
        ).fetchall()


def list_acudit_texts(limit: int) -> list[str]:
    """Textos dels acudits més recents (per passar-los a Claude com a context
    perquè no els repeteixi)."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT text FROM acudits ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [r["text"] for r in rows]


def count_acudits() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM acudits").fetchone()["n"]


def delete_acudit(acudit_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM acudits WHERE id = ?", (acudit_id,))
        conn.commit()
        return cur.rowcount > 0

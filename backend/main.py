"""Aplicació FastAPI: generador d'acudits amb Claude i base de dades SQLite.

Rutes:
  GET  /              → serveix la web (frontend/)
  POST /api/generar   → genera un acudit amb Claude; si ja existeix a la BD no
                        l'afegeix, si és nou l'afegeix. Tornem l'acudit i si era nou.
  GET  /api/acudits   → llista tots els acudits desats a la BD
  DELETE /api/acudits/{id} → esborra un acudit
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import ai, config, db

app = FastAPI(title="Generador d'Acudits")


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


def _acudit_dict(row) -> dict:
    return {"id": row["id"], "text": row["text"], "created_at": row["created_at"]}


# ─── API ────────────────────────────────────────────────────
class GenerarBody(BaseModel):
    tema: str = ""


@app.post("/api/generar")
async def generar(body: GenerarBody) -> JSONResponse:
    # Acudits ja existents → es passen a Claude perquè no els repeteixi
    existents = db.list_acudit_texts(config.MAX_CONTEXT_JOKES)

    ok, acudit, error = await ai.generar_acudit(body.tema, existents)
    if not ok:
        return JSONResponse({"ok": False, "error": error}, status_code=502)

    # Comprova a la BD: si ja hi és no l'afegeix; si no, l'afegeix
    row, es_nou = db.add_acudit(acudit)
    if row is None:
        return JSONResponse(
            {"ok": False, "error": "Claude ha tornat un acudit buit."}, status_code=502
        )

    return JSONResponse(
        {
            "ok": True,
            "nou": es_nou,           # True = afegit a la BD; False = ja existia
            "acudit": _acudit_dict(row),
            "total": db.count_acudits(),
        }
    )


@app.get("/api/acudits")
def llistar() -> JSONResponse:
    rows = db.list_acudits()
    return JSONResponse(
        {"ok": True, "total": len(rows), "acudits": [_acudit_dict(r) for r in rows]}
    )


@app.delete("/api/acudits/{acudit_id}")
def esborrar(acudit_id: int) -> JSONResponse:
    esborrat = db.delete_acudit(acudit_id)
    return JSONResponse({"ok": esborrat})


# ─── Frontend estàtic ───────────────────────────────────────
# Es munta a l'arrel DESPRÉS de les rutes /api, així aquestes tenen prioritat.
# html=True fa que "/" serveixi automàticament frontend/index.html.
app.mount("/", StaticFiles(directory=str(config.FRONTEND_DIR), html=True), name="frontend")

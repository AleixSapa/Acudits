# Generador d'Acudits 😄

Web que genera acudits amb **Claude** (el del servidor, via subscripció — sense API key)
i els desa en una base de dades **SQLite**, evitant duplicats.

- En generar un acudit, comprova si **ja existeix** a la base de dades:
  - si **no** hi és → l'afegeix,
  - si **ja** hi és → no l'afegeix (t'avisa que ja el tenies).
- Pots **llegir** tots els acudits desats i esborrar-ne.

## Estructura

```
Acudits/
├── Dockerfile            ← imatge per a Dokploy (a l'arrel)
├── requirements.txt
├── backend/              ← API FastAPI + connexió amb Claude
│   ├── main.py           ← rutes HTTP i serveix el frontend
│   ├── ai.py             ← invoca `claude -p` (subprocess, prompt per STDIN)
│   ├── db.py             ← capa SQLite (detecció de duplicats)
│   └── config.py         ← configuració per variables d'entorn
├── frontend/             ← web estàtica (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   └── app.js
└── data/                 ← base de dades SQLite (volum persistent)
```

## Com es connecta amb Claude

El `Dockerfile` instal·la **Claude Code** dins del contenidor (`npm install -g
@anthropic-ai/claude-code`) i el backend l'executa amb
`claude -p --permission-mode bypassPermissions` (el prompt es passa per STDIN).
L'autenticació s'obté **muntant les credencials del host** dins del contenidor.

## Desplegament a Dokploy

1. Crea una aplicació nova a Dokploy apuntant a aquest repositori (Build type: **Dockerfile**).
2. A **Advanced → Volumes** afegeix dos muntatges:

   | Tipus | Origen (host) | Destí (contenidor) |
   |-------|----------------|--------------------|
   | **Bind Mount** | `/home/esanpons/.claude` | `/root/.claude` |
   | **Volume Mount** | `acudits-data` | `/app/data` |

   - El *bind mount* dóna a Claude del contenidor les credencials del servidor.
   - El *volume mount* fa que la base de dades SQLite no es perdi entre desplegaments.
3. (Opcional) A **Environment** pots ajustar `CLAUDE_MODEL`, `AI_TIMEOUT`, etc. (vegeu `.env.example`).
4. Configura el domini apuntant al port intern **8200** (port lliure al servidor) i desplega.

## Endpoints

- `GET /` — la web.
- `POST /api/generar` — body `{"tema": "opcional"}` → genera, desa si és nou.
  Resposta: `{ ok, nou, acudit: {id, text, created_at}, total }`.
- `GET /api/acudits` — llista tots els acudits.
- `DELETE /api/acudits/{id}` — esborra un acudit.

## Provar en local

Cal tenir Claude Code instal·lat i autenticat a la màquina:

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8200
# obre http://localhost:8200
```

# Generador d'Acudits — imatge per a Dokploy
# Python (FastAPI) + Node amb Claude Code instal·lat dins del contenidor.
FROM python:3.12-slim

# ─── Node 20 + Claude Code ──────────────────────────────────
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && npm install -g @anthropic-ai/claude-code \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependències de Python (capa cau abans de copiar el codi)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Codi de l'aplicació (backend/ i frontend/)
COPY . .

# Port intern del contenidor. 8200 està lliure al servidor (3000 l'usen Dokploy i generar-fitxes).
ENV PORT=8200
# El contenidor és un entorn aïllat: permet a Claude Code el bypass de permisos com a root
ENV IS_SANDBOX=1
EXPOSE 8200

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]

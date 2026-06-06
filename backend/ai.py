"""Invocació del CLI de Claude Code per generar un acudit.

S'executa `claude -p --permission-mode bypassPermissions` com a subprocess i el
prompt es passa per STDIN (no com a argument, per evitar problemes de cometes i
de longitud). Cal que el contenidor tingui Claude Code instal·lat i les credencials
muntades a /root/.claude (vegeu el README i la configuració de Dokploy).
"""
from __future__ import annotations

import asyncio
import shlex

from . import config

_QUALITAT = (
    "Vull un acudit REALMENT bo, que faci riure de veritat — no un de tòpic ni dolent. "
    "Pautes:\n"
    "- Que tingui una gràcia clara: un remat (punchline) enginyós, sorprenent o absurd "
    "que canviï el sentit de cop.\n"
    "- Aprofita jocs de paraules, dobles sentits o girs inesperats en català.\n"
    "- Evita els acudits més gastats i previsibles (els que tothom ja coneix).\n"
    "- Varia el format: pot ser pregunta-resposta, una situació curta, un diàleg, etc. "
    "No sempre comencis amb «Per què...».\n"
    "- Ha de ser curt i entenedor, i el remat ha d'arribar de pressa.\n"
    "- Abans de respondre, assegura't que de debò té gràcia; si no, pensa'n un de millor."
)

_ONLY_JOKE = (
    "MOLT IMPORTANT: respon NOMÉS amb el text de l'acudit, en català. "
    "No escriguis cap introducció, títol, explicació, valoració, ni cometes ni guions al davant. "
    "Comença directament per l'acudit."
)


def _build_argv() -> list[str]:
    """Construeix l'argv per llançar Claude Code en mode headless."""
    raw = shlex.split(config.CLAUDE_CMD)
    argv = raw + ["-p", "--permission-mode", "bypassPermissions"]
    if config.CLAUDE_MODEL:
        argv += ["--model", config.CLAUDE_MODEL]
    return argv


def build_prompt(tema: str, existents: list[str]) -> str:
    parts: list[str] = []
    if tema.strip():
        parts.append(f"Explica un acudit en català sobre: {tema.strip()}.")
    else:
        parts.append("Explica un acudit en català, de temàtica lliure.")

    parts.append("")
    parts.append(_QUALITAT)

    if existents:
        parts.append("")
        parts.append(
            "NO repeteixis cap d'aquests acudits que ja tinc (ni cap de molt semblant). "
            "Fes-ne un de NOU i diferent:"
        )
        parts += [f"- {a}" for a in existents]

    parts.append("")
    parts.append(_ONLY_JOKE)
    return "\n".join(parts)


async def _run(prompt: str) -> tuple[int, str, str]:
    argv = _build_argv()
    proc = await asyncio.create_subprocess_exec(
        *argv,
        cwd=str(config.BASE_DIR),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=prompt.encode("utf-8")),
            timeout=config.AI_TIMEOUT,
        )
    except asyncio.TimeoutError:
        proc.kill()
        return 124, "", f"Temps esgotat ({config.AI_TIMEOUT}s)."
    return (
        proc.returncode or 0,
        stdout.decode("utf-8", "replace"),
        stderr.decode("utf-8", "replace"),
    )


def _clean(text: str) -> str:
    """Neteja la resposta: treu cometes/guions inicials i espais sobrants."""
    text = (text or "").strip()
    # Treu un possible embolcall de cometes
    if len(text) >= 2 and text[0] in "\"'«" and text[-1] in "\"'»":
        text = text[1:-1].strip()
    return text


async def generar_acudit(tema: str, existents: list[str]) -> tuple[bool, str, str]:
    """Genera un acudit amb Claude.

    Retorna (ok, acudit, error).
    """
    prompt = build_prompt(tema, existents)
    try:
        code, stdout, stderr = await _run(prompt)
    except FileNotFoundError:
        return False, "", "No s'ha trobat el CLI «claude» al contenidor."
    except Exception as exc:  # noqa: BLE001
        return False, "", f"Error executant Claude: {exc}"

    acudit = _clean(stdout)
    if acudit:
        return True, acudit, ""
    return False, "", (stderr.strip() or f"Claude ha retornat el codi {code}.")[:500]

"use strict";

const $ = (sel) => document.querySelector(sel);

const inputTema = $("#tema");
const btnGenerar = $("#btn-generar");
const btnRefresca = $("#btn-refresca");
const llista = $("#llista");
const comptador = $("#comptador");
const llistaBuida = $("#llista-buida");
const toggleLlista = $("#toggle-llista");
const cosLlista = $("#cos-llista");
const fletxa = $("#fletxa");
const modal = $("#modal");
const modalContingut = $("#modal-contingut");
const modalTanca = $("#modal-tanca");

// Acudits carregats (id → text) per poder mostrar-los al modal en clicar-los
const acuditsCache = new Map();

// Escapa text per evitar injecció d'HTML
function esc(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

// ─── Finestra (modal) ───────────────────────────────────────
function obreModal(html) {
  modalContingut.innerHTML = html;
  modal.classList.remove("oculta");
}
function tancaModal() {
  modal.classList.add("oculta");
}

// ─── Generar un acudit ──────────────────────────────────────
async function generar() {
  btnGenerar.disabled = true;
  obreModal("Pensant un acudit… 🤔");

  try {
    const resp = await fetch("/api/generar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tema: inputTema.value }),
    });
    const data = await resp.json();

    if (!data.ok) {
      obreModal(
        `<span class="etiqueta error">Error</span><div>${esc(data.error || "Error desconegut")}</div>`
      );
      return;
    }

    const etiqueta = data.nou
      ? `<span class="etiqueta nou">Nou · afegit</span>`
      : `<span class="etiqueta repe">Ja el tenies · no s'afegeix</span>`;
    obreModal(`${etiqueta}<div>${esc(data.acudit.text)}</div>`);

    await carregaLlista();
  } catch (e) {
    obreModal(
      `<span class="etiqueta error">Error</span><div>No s'ha pogut connectar amb el servidor.</div>`
    );
  } finally {
    btnGenerar.disabled = false;
  }
}

// ─── Llistar acudits desats ─────────────────────────────────
async function carregaLlista() {
  try {
    const resp = await fetch("/api/acudits");
    const data = await resp.json();
    const acudits = data.acudits || [];
    comptador.textContent = acudits.length;
    llista.innerHTML = "";
    acuditsCache.clear();
    llistaBuida.style.display = acudits.length ? "none" : "block";

    for (const a of acudits) {
      acuditsCache.set(String(a.id), a.text);
      const li = document.createElement("li");
      li.innerHTML =
        `<button class="acudit-mini" data-id="${a.id}" title="Mostra l'acudit">${esc(a.text)}</button>` +
        `<button class="esborra" title="Esborra" data-id="${a.id}">🗑️</button>`;
      llista.appendChild(li);
    }
  } catch (e) {
    /* silenci: es tornarà a provar amb el botó Actualitza */
  }
}

// ─── Clics dins la llista (mostrar o esborrar) ──────────────
llista.addEventListener("click", async (ev) => {
  const mini = ev.target.closest(".acudit-mini");
  if (mini) {
    const text = acuditsCache.get(mini.dataset.id);
    if (text) obreModal(`<div>${esc(text)}</div>`);
    return;
  }
  const btn = ev.target.closest(".esborra");
  if (!btn) return;
  if (!confirm("Segur que vols esborrar aquest acudit?")) return;
  await fetch(`/api/acudits/${btn.dataset.id}`, { method: "DELETE" });
  await carregaLlista();
});

// ─── Desplegar / plegar la llista d'acudits desats ──────────
toggleLlista.addEventListener("click", () => {
  const obert = cosLlista.classList.toggle("oculta") === false;
  toggleLlista.setAttribute("aria-expanded", String(obert));
});

btnGenerar.addEventListener("click", generar);
btnRefresca.addEventListener("click", carregaLlista);
inputTema.addEventListener("keydown", (e) => {
  if (e.key === "Enter") generar();
});

// Tancar el modal: botó ✕, clic al fons fosc, o tecla Escape
modalTanca.addEventListener("click", tancaModal);
modal.addEventListener("click", (e) => {
  if (e.target === modal) tancaModal();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") tancaModal();
});

// Càrrega inicial
carregaLlista();

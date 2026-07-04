// app.js - frontend del Buscador Universal.
// Carga el catalogo de fuentes, muestra sus enlaces y consume el endpoint SSE.

const $ = (sel) => document.querySelector(sel);

const hero = $("#hero");
const form = $("#form");
const inputQ = $("#q");
const btn = $("#btn");
const panel = $("#panel-fuentes");
const contFuentes = $("#fuentes");
const estado = $("#estado");
const resultados = $("#resultados");
const dtv = $("#dtv");

let CATALOGO = [];
let INDIRECTAS = [];
let fuenteEvt = null;
let esperadas = 0;
let recibidas = 0;

function esc(valor) {
  return String(valor ?? "").replace(/[&<>"]/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
  })[c]);
}

function host(url) {
  try {
    return new URL(url).host.replace(/^www\./, "");
  } catch {
    return url || "";
  }
}

async function cargarFuentes() {
  const r = await fetch("/api/fuentes");
  const data = await r.json();

  CATALOGO = data.fuentes || [];
  INDIRECTAS = data.indirectas || [];

  $("#n-fuentes").textContent = CATALOGO.length;
  $("#hero-copy").textContent = `Busca a una persona en ${CATALOGO.length} fuentes del terremoto de Venezuela 2026, a la vez.`;
  contFuentes.innerHTML = CATALOGO.map((f) => `
    <label class="fuente-item" title="${esc(f.descripcion)}">
      <input type="checkbox" value="${esc(f.key)}" checked>
      <span class="nom">${esc(f.label)}${f.requiere_token ? ' <span class="tk">token</span>' : ""}</span>
      ${f.sitio ? `<a class="ext" href="${esc(f.sitio)}" target="_blank" rel="noopener" title="Abrir ${esc(host(f.sitio))}">↗</a>` : ""}
    </label>
  `).join("");

  $("#cat-directas").innerHTML = CATALOGO.map((f) => `
    <li>
      <a href="${esc(f.sitio)}" target="_blank" rel="noopener">${esc(f.label)}</a>
      <span class="via">${esc(host(f.sitio))} · ${esc(f.descripcion)}</span>
    </li>
  `).join("");

  $("#cat-indirectas").innerHTML = INDIRECTAS.map((f) => `
    <li>
      <a href="${esc(f.sitio)}" target="_blank" rel="noopener">${esc(f.nombre)}</a>
      <span class="via">${esc(host(f.sitio))} · ${esc(f.via)}</span>
    </li>
  `).join("");
}

function togglePanel(forzar) {
  const abrir = forzar !== undefined ? forzar : panel.classList.contains("oculto");
  panel.classList.toggle("oculto", !abrir);
}

$("#toggle-fuentes").addEventListener("click", () => togglePanel());
$("#ver-fuentes").addEventListener("click", (e) => {
  e.preventDefault();
  togglePanel(true);
});

document.addEventListener("click", (e) => {
  const a = e.target.closest("[data-all]");
  if (!a) return;

  e.preventDefault();
  const val = a.dataset.all === "1";
  contFuentes.querySelectorAll("input[type=checkbox]").forEach((c) => {
    c.checked = val;
  });
});

function seleccion() {
  return [...contFuentes.querySelectorAll("input:checked")].map((c) => c.value);
}

function bloqueFuente(f) {
  const div = document.createElement("div");
  div.className = "fuente-bloque";
  div.id = "bloque_" + f.key;
  div.innerHTML = `
    <div class="fuente-cab">
      <span class="izq">
        <span class="nombre">${esc(f.label)}</span>
        ${f.sitio ? `<a class="sitio" href="${esc(f.sitio)}" target="_blank" rel="noopener">${esc(host(f.sitio))} ↗</a>` : ""}
      </span>
      <span class="conteo" id="conteo_${esc(f.key)}">buscando...</span>
    </div>
    <div class="tarjetas" id="tarjetas_${esc(f.key)}"></div>
  `;

  div.querySelector(".fuente-cab").addEventListener("click", (e) => {
    if (e.target.closest("a")) return;
    const t = div.querySelector(".tarjetas");
    t.style.display = t.style.display === "none" ? "" : "none";
  });

  return div;
}

function tarjeta(h) {
  const meta = [];
  if (h.edad) meta.push(`edad <b>${esc(h.edad)}</b>`);
  if (h.cedula) meta.push(`C.I. <b>${esc(h.cedula)}</b>`);
  if (h.lugar) meta.push(esc(h.lugar));

  const badge = h.estado ? `<span class="badge">${esc(h.estado)}</span>` : "";
  const ver = h.url ? `<a class="ver" href="${esc(h.url)}" target="_blank" rel="noopener">ver ficha ↗</a>` : "";

  return `<div class="tarjeta">
    <div class="nom">${esc(h.nombre || "(sin nombre)")}${badge}</div>
    ${meta.length ? `<div class="meta">${meta.join(" · ")}</div>` : ""}
    ${ver}
  </div>`;
}

function pintarEvento(ev) {
  const cab = $("#conteo_" + ev.fuente);
  const caja = $("#tarjetas_" + ev.fuente);
  if (!cab || !caja) return;

  if (ev.error) {
    cab.textContent = "omitida";
    cab.className = "conteo err";
    caja.innerHTML = `<div class="err-msg">${esc(ev.error)}</div>`;
    return;
  }

  const n = ev.resultados.length;
  cab.textContent = n === 0 ? "sin coincidencias" : `${n} resultado${n === 1 ? "" : "s"}`;
  cab.className = "conteo" + (n ? " hay" : "");
  caja.innerHTML = n ? ev.resultados.map(tarjeta).join("") : "";
  if (!n) caja.style.display = "none";
}

function actualizarProgreso() {
  const pct = esperadas ? Math.round((recibidas / esperadas) * 100) : 0;
  estado.innerHTML = `Consultando ${recibidas}/${esperadas} fuentes...
    <div class="barra"><i style="width:${pct}%"></i></div>`;
}

function buscar(query) {
  if (fuenteEvt) fuenteEvt.close();

  const sel = seleccion();
  if (!sel.length) {
    togglePanel(true);
    estado.textContent = "Selecciona al menos una fuente.";
    return;
  }

  hero.classList.add("compacto");
  resultados.innerHTML = "";
  esperadas = sel.length;
  recibidas = 0;
  btn.disabled = true;

  const orden = CATALOGO.filter((f) => sel.includes(f.key));
  for (const f of orden) {
    resultados.appendChild(bloqueFuente(f));
  }

  actualizarProgreso();

  const params = new URLSearchParams({ q: query, fuentes: sel.join(",") });
  if (dtv && dtv.value.trim()) params.set("dtv_token", dtv.value.trim());

  fuenteEvt = new EventSource("/api/buscar?" + params.toString());
  let totalHits = 0;

  fuenteEvt.onmessage = (m) => {
    const ev = JSON.parse(m.data);
    if (ev.fin) {
      fuenteEvt.close();
      btn.disabled = false;
      estado.innerHTML = `Listo · <b>${totalHits}</b> coincidencia${totalHits === 1 ? "" : "s"} en ${esperadas} fuentes.`;
      return;
    }

    recibidas++;
    if (!ev.error) totalHits += ev.resultados.length;
    pintarEvento(ev);
    actualizarProgreso();
  };

  fuenteEvt.onerror = () => {
    fuenteEvt.close();
    btn.disabled = false;
    estado.textContent = "Se interrumpio la conexion con el servidor.";
  };
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const q = inputQ.value.trim();
  if (q) buscar(q);
});

$("#copiar").addEventListener("click", () => {
  navigator.clipboard.writeText($("#snippet").textContent.trim());
  $("#copiar").textContent = "copiado";
  setTimeout(() => {
    $("#copiar").textContent = "copiar";
  }, 1500);
});

cargarFuentes().catch(() => {
  estado.textContent = "No se pudo cargar el catalogo de fuentes.";
});

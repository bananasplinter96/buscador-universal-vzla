"""
busqueda — orquestador que consulta las fuentes en paralelo.

Ofrece dos modos:
  · buscar()        → espera a todas y devuelve un resultado agregado.
  · buscar_stream() → generador que emite cada fuente en cuanto termina
                      (ideal para Server-Sent Events / feedback incremental).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator

from .core import normalizar
from .registro import FUENTES


def _seleccionar(fuentes) -> list[str]:
    if not fuentes:
        return list(FUENTES)
    if isinstance(fuentes, str):
        fuentes = fuentes.split(",")
    return [f.strip() for f in fuentes if f.strip() in FUENTES]


def _ejecutar(key: str, query: str, qn: str, ctx: dict) -> list[dict]:
    resultados = FUENTES[key].fn(query, qn, ctx) or []
    for r in resultados:
        r.setdefault("fuente", key)
    return resultados


def buscar_stream(query: str, fuentes=None, ctx: dict | None = None) -> Iterator[dict]:
    """Emite un dict por fuente conforme va terminando:

        {"fuente": str, "label": str, "resultados": [...], "error": str|None}
    """
    ctx = ctx or {}
    seleccion = _seleccionar(fuentes)
    qn = normalizar(query)
    with ThreadPoolExecutor(max_workers=min(len(seleccion) or 1, 12)) as ex:
        futs = {ex.submit(_ejecutar, k, query, qn, ctx): k for k in seleccion}
        for fut in as_completed(futs):
            key = futs[fut]
            evento = {"fuente": key, "label": FUENTES[key].label,
                      "resultados": [], "error": None}
            try:
                evento["resultados"] = fut.result()
            except Exception as e:
                evento["error"] = f"{type(e).__name__}: {e}"
            yield evento


def buscar(query: str, fuentes=None, ctx: dict | None = None) -> dict:
    """Versión agregada (bloqueante). Devuelve:

        {"query": str, "total": int, "por_fuente": {key: [...]},
         "errores": {key: str}}
    """
    por_fuente, errores, total = {}, {}, 0
    for ev in buscar_stream(query, fuentes, ctx):
        if ev["error"]:
            errores[ev["fuente"]] = ev["error"]
        else:
            por_fuente[ev["fuente"]] = ev["resultados"]
            total += len(ev["resultados"])
    return {"query": query, "total": total,
            "por_fuente": por_fuente, "errores": errores}
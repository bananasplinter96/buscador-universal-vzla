"""
core — utilidades de texto y HTTP compartidas por todas las fuentes.
"""

from __future__ import annotations

import unicodedata

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36")
TIMEOUT = 30


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

def http_get(url: str, headers: dict | None = None, **kw) -> requests.Response:
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    return requests.get(url, headers=h, timeout=TIMEOUT, **kw)


def http_post(url: str, headers: dict | None = None, **kw) -> requests.Response:
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    return requests.post(url, headers=h, timeout=TIMEOUT, **kw)


# --------------------------------------------------------------------------
# Texto
# --------------------------------------------------------------------------

def normalizar(s) -> str:
    """minúsculas, sin acentos, espacios colapsados."""
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.lower().split())


def coincide(query_norm: str, texto) -> bool:
    """True si TODOS los tokens del query aparecen en el texto normalizado."""
    t = normalizar(texto)
    return all(tok in t for tok in query_norm.split())


def es_cedula(q: str) -> bool:
    limpio = cedula_num(q)
    return limpio.isdigit() and len(limpio) >= 5


def cedula_num(q: str) -> str:
    return str(q or "").replace(".", "").replace("-", "").strip().lstrip("VvEe")


def limpiar_cedula(valor) -> str:
    return str(valor or "").replace(".", "").replace("-", "")

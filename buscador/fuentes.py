"""
fuentes — implementación de cada plataforma consultada en vivo.

Dos grupos:
  · GRUPO_NATIVO: el servidor ofrece búsqueda por ?q= (rápido y dirigido).
  · GRUPO_DUMP:   no hay buscador; se descarga el dataset (o el fragmento
                  correspondiente) y se filtra localmente.

Todas las llamadas son de solo lectura.
"""

from __future__ import annotations

import html as html_mod
import json
import re

from .core import (cedula_num, coincide, es_cedula, http_get, http_post,
                   limpiar_cedula)
from .registro import GRUPO_DUMP, GRUPO_NATIVO, registrar

# Credenciales públicas (anon key / site key visibles en el front de cada sitio)
_HEV_URL = "https://ozuxfepfkvnxkywdsqxy.supabase.co"
_HEV_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im96dXhmZXBma3ZueGt5d2RzcXh5Ii"
    "wicm9sZSI6ImFub24iLCJpYXQiOjE3ODI0MjI5NTEsImV4cCI6MjA5Nzk5ODk1MX0"
    ".YhW0GalGkQZdO2NJTg_01C5XhdMmJ6RbNSNXXC0xG4o"
)

# Site key reCAPTCHA v3 de desaparecidosterremotovenezuela.com (pública)
DTV_SITE_KEY = "6LeBfDUtAAAAAMw1Wtkd58bst6vEnLOi3_NAjGD0"


# ===========================================================================
# GRUPO A — buscadores nativos (server-side ?q=)
# ===========================================================================

@registrar("venezuelareporta", "Venezuela Reporta",
           "API buscar?q= (nativo)", GRUPO_NATIVO,
           sitio="https://venezuelareporta.org/")
def venezuelareporta(query, qn, ctx):
    r = http_get("https://venezuelareporta.org/api/buscar", params={"q": query})
    r.raise_for_status()
    return [{
        "nombre": p.get("nombre"),
        "estado": p.get("status"),
        "lugar": p.get("ciudad"),
        "url": f"https://venezuelareporta.org/reporte/{p.get('id')}",
    } for p in r.json().get("resultados", [])]


@registrar("hazlohoy", "Hazlo Hoy (agregador)",
           "SSR /buscar?q=; integra venezuelatebusca + desaparecidosterremoto + terremotoVE",
           GRUPO_NATIVO, sitio="https://terremoto.hazlohoy.org/")
def hazlohoy(query, qn, ctx):
    r = http_get("https://terremoto.hazlohoy.org/buscar",
                 params={"q": query, "ciudad": ""})
    r.raise_for_status()
    texto = re.sub(r"<script[^>]*>.*?</script>", "", r.text, flags=re.S)
    texto = html_mod.unescape(re.sub(r"<[^>]+>", "\n", texto))
    out, actual = [], None
    for linea in (l.strip() for l in texto.splitlines() if l.strip()):
        if linea.startswith("\U0001F3E2"):  # 🏢
            continue
        if "Fuente:" in linea:
            if actual:
                origen = linea.split("Fuente:", 1)[1].split("·")[0].strip()
                out.append({"nombre": actual, "estado": "ver ficha",
                            "lugar": f"(fuente original: {origen})", "url": r.url})
                actual = None
            continue
        if (2 <= len(linea.split()) <= 8 and not any(c.isdigit() for c in linea)
                and coincide(qn, linea)):
            actual = linea
    return out


@registrar("aquiestoyvenezuela", "Aquí Estoy Venezuela",
           "~66k · personas.php?q= (nativo abierto)", GRUPO_NATIVO,
           sitio="https://aquiestoyvenezuela.com/")
def aquiestoyvenezuela(query, qn, ctx):
    r = http_get("https://aquiestoyvenezuela.com/db-reader/personas.php",
                 params={"q": query, "limit": 100},
                 headers={"Accept": "application/json"})
    r.raise_for_status()
    return [{
        "nombre": p.get("nombre"), "edad": p.get("edad"), "cedula": p.get("cedula"),
        "estado": p.get("estado"), "lugar": p.get("ultima_ubicacion") or p.get("ciudad"),
        "url": "https://aquiestoyvenezuela.com/",
    } for p in r.json().get("records", [])]


@registrar("localizapacientes", "Localiza Pacientes",
           "/api/search?q= (nativo, cap 50)", GRUPO_NATIVO,
           sitio="https://localizapacientes.com/")
def localizapacientes(query, qn, ctx):
    r = http_get("https://localizapacientes.com/api/search",
                 params={"q": query}, headers={"Accept": "application/json"})
    r.raise_for_status()
    return [{
        "nombre": p.get("nombreCompleto"), "edad": p.get("edad"),
        "estado": p.get("condicion") or p.get("estado"),
        "lugar": p.get("hospital") or p.get("ciudad"),
        "url": "https://localizapacientes.com/",
    } for p in r.json().get("resultados", [])]


@registrar("tebusco", "Te Busco",
           "POST portero {op:buscar} (nativo, cap 80)", GRUPO_NATIVO,
           sitio="https://www.tebusco.app/")
def tebusco(query, qn, ctx):
    r = http_post("https://www.tebusco.app/tebusco-portero.php",
                  headers={"Content-Type": "application/json",
                           "Accept": "application/json"},
                  data=json.dumps({"op": "buscar", "q": query}))
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        return []
    return [{
        "nombre": p.get("name"), "cedula": p.get("cid"),
        "estado": p.get("state"), "lugar": p.get("place"),
        "url": "https://www.tebusco.app/",
    } for p in data]


@registrar("hospitalesenvenezuela", "Hospitales en Venezuela",
           "RPC Supabase buscar_paciente (mín. 3 letras)", GRUPO_NATIVO,
           sitio="https://hospitalesenvenezuela.com/")
def hospitalesenvenezuela(query, qn, ctx):
    if len(query.strip()) < 3:
        return []
    r = http_post(f"{_HEV_URL}/rest/v1/rpc/buscar_paciente",
                  headers={"apikey": _HEV_KEY, "Authorization": f"Bearer {_HEV_KEY}",
                           "Content-Type": "application/json", "Accept": "application/json"},
                  data=json.dumps({"p_term": query}))
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        return []
    return [{
        "nombre": p.get("nombre"), "cedula": p.get("cedula"),
        "estado": p.get("condicion"), "lugar": p.get("centro"),
        "url": "https://hospitalesenvenezuela.com/",
    } for p in data]


@registrar("desaparecidos_terremoto", "Desaparecidos Terremoto Venezuela",
           "~46k · API q= server-side (reCAPTCHA v3 · requiere token)",
           GRUPO_NATIVO, sitio="https://desaparecidosterremotovenezuela.com/",
           requiere_token=True)
def desaparecidos_terremoto(query, qn, ctx):
    """La API filtra por ?q= pero exige un token reCAPTCHA v3 fresco (~2 min).
    El token se pasa en ctx['dtv_token'] (ver README, sección reCAPTCHA)."""
    token = (ctx or {}).get("dtv_token")
    if not token:
        raise RuntimeError(
            "requiere token reCAPTCHA (ver README). Se omite; "
            "hazlohoy ya agrega esta fuente indirectamente.")
    r = http_get("https://desaparecidos-terremoto-api.theempire.tech/api/personas",
                 params={"page": 1, "pageSize": 50, "q": query},
                 headers={"x-recaptcha-token": token,
                          "origin": "https://desaparecidosterremotovenezuela.com",
                          "referer": "https://desaparecidosterremotovenezuela.com/",
                          "accept": "*/*"})
    if r.status_code == 403:
        raise RuntimeError("token reCAPTCHA rechazado o expirado — genera uno nuevo")
    r.raise_for_status()
    return [{
        "nombre": p.get("nombre"), "edad": p.get("edad"), "cedula": p.get("cedula"),
        "estado": p.get("estado"), "lugar": p.get("ubicacion"),
        "url": "https://desaparecidosterremotovenezuela.com/",
    } for p in r.json().get("items", [])]


# ===========================================================================
# GRUPO B — descarga del dataset (o fragmento) + filtro local
# ===========================================================================

@registrar("sosven", "SOS Venezuela", "~7k · dump completo", GRUPO_DUMP, sitio="https://sosven.site/")
def sosven(query, qn, ctx):
    r = http_get("https://sosven.site/api.php?action=listar")
    r.raise_for_status()
    ced = cedula_num(query) if es_cedula(query) else None
    out = []
    for p in r.json():
        if p.get("tipo") != "persona":
            continue
        pc = limpiar_cedula(p.get("cedula"))
        blob = " ".join(str(p.get(k, "")) for k in
                        ("nombre", "cedula", "ciudad", "localidad", "descripcion"))
        if (ced and ced in pc) or coincide(qn, blob):
            out.append({"nombre": p.get("nombre"), "edad": p.get("edad"),
                        "cedula": p.get("cedula"), "estado": p.get("estatus"),
                        "lugar": p.get("ciudad") or p.get("localidad"),
                        "url": "https://sosven.site/"})
    return out


@registrar("desaparecidosvenezuela", "Desaparecidos Venezuela",
           "~1.4k · paginado /api/personas?skip=", GRUPO_DUMP, sitio="https://www.desaparecidosvenezuela.com/")
def desaparecidosvenezuela(query, qn, ctx):
    out, skip = [], 0
    while True:
        r = http_get("https://www.desaparecidosvenezuela.com/api/personas",
                     params={"skip": skip})
        r.raise_for_status()
        page = r.json()
        if not isinstance(page, list) or not page:
            break
        for p in page:
            blob = " ".join(str(p.get(k, "")) for k in ("nombre", "zona", "descripcion"))
            if coincide(qn, blob):
                out.append({"nombre": p.get("nombre"), "edad": p.get("edad"),
                            "estado": f"{p.get('estado')}/{p.get('tipo')}",
                            "lugar": p.get("zona"),
                            "url": "https://www.desaparecidosvenezuela.com/"})
        if len(page) < 20:
            break
        skip += 20
    return out


@registrar("busquedavzla", "Búsqueda VZLA", "dump completo /api/reports", GRUPO_DUMP, sitio="https://busquedavzla.netlify.app/")
def busquedavzla(query, qn, ctx):
    r = http_get("https://busquedavzla.netlify.app/api/reports")
    r.raise_for_status()
    data = r.json()
    reports = data if isinstance(data, list) else data.get("reports", data.get("items", []))
    return [{
        "nombre": p.get("nombre") or p.get("name") or p.get("fullName"),
        "estado": p.get("estado") or p.get("status"),
        "lugar": p.get("ubicacion") or p.get("location") or p.get("ciudad"),
        "url": "https://busquedavzla.netlify.app/",
    } for p in (reports or []) if coincide(qn, json.dumps(p, ensure_ascii=False))]


@registrar("ucv_aparecidos", "UCV Aparecidos", "~1k · estudiantes UCV", GRUPO_DUMP, sitio="https://ucv-aparecidos.vercel.app/")
def ucv_aparecidos(query, qn, ctx):
    r = http_get("https://ucv-aparecidos.vercel.app/api/estudiantes")
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        return []
    ced = cedula_num(query) if es_cedula(query) else None
    out = []
    for p in data:
        pc = limpiar_cedula(p.get("cedula"))
        blob = " ".join(str(p.get(k, "")) for k in
                        ("nombre", "cedula", "ultima_ubicacion", "descripcion",
                         "carrera", "facultad"))
        if (ced and ced in pc) or coincide(qn, blob):
            out.append({"nombre": p.get("nombre"), "cedula": p.get("cedula"),
                        "estado": p.get("estado"), "lugar": p.get("ultima_ubicacion"),
                        "url": "https://ucv-aparecidos.vercel.app/"})
    return out


@registrar("localizadosvenezuela", "Localizados Venezuela",
           "~4.4k · paginado /api/v1/localizados", GRUPO_DUMP, sitio="https://localizadosvenezuela.com/")
def localizadosvenezuela(query, qn, ctx):
    out, page = [], 1
    tope = (ctx or {}).get("max_paginas", 50)
    while page <= tope:
        r = http_get("https://localizadosvenezuela.com/api/v1/localizados",
                     params={"page": page, "limit": 100},
                     headers={"Accept": "application/json"})
        r.raise_for_status()
        data = r.json()
        for p in data.get("data", []):
            blob = " ".join(str(p.get(k, "")) for k in
                            ("nombreCompleto", "direccion", "observaciones", "lugarNombre"))
            if coincide(qn, blob):
                out.append({"nombre": p.get("nombreCompleto"), "estado": p.get("condicion"),
                            "lugar": p.get("lugarNombre") or p.get("direccion"),
                            "url": f"https://localizadosvenezuela.com/p/{p.get('slug','')}"})
        if page >= data.get("meta", {}).get("totalPages", 1):
            break
        page += 1
    return out


@registrar("ubicame", "911 Ubícame",
           "~44k · shards estáticos por letra inicial", GRUPO_DUMP, sitio="https://911.ubica.me/")
def ubicame(query, qn, ctx):
    """Los registros están en archivos por letra inicial del nombre. Se bajan
    solo los shards de la(s) primera(s) letra(s) de las palabras del query."""
    letras = {w[0].upper() for w in qn.split() if w and w[0].isalpha()}
    ced = cedula_num(query) if es_cedula(query) else None
    if ced and not letras:
        return []  # cédula sola: sin letra no podemos elegir shard
    out = []
    for letra in sorted(letras):
        try:
            r = http_get(f"https://911.ubica.me/public/data/{letra}.json",
                         headers={"Accept": "application/json"})
            if r.status_code != 200:
                continue
            raw = r.content
            if raw[:3] == b"\xef\xbb\xbf":
                raw = raw[3:]
            registros = json.loads(raw.decode("utf-8"))
        except Exception:
            continue
        for p in registros:
            pc = limpiar_cedula(p.get("ext_venezuela_ci"))
            blob = " ".join(str(p.get(k, "")) for k in
                            ("full_name", "ext_venezuela_ci", "last_known_location", "notes"))
            if (ced and ced in pc) or coincide(qn, blob):
                out.append({"nombre": p.get("full_name"), "edad": p.get("age"),
                            "cedula": p.get("ext_venezuela_ci"), "estado": p.get("status"),
                            "lugar": p.get("last_known_location"),
                            "url": "https://911.ubica.me/"})
    return out


@registrar("encuentralos", "Encuéntralos",
           "97k · paginado (limitado por max_paginas)", GRUPO_DUMP,
           sitio="https://encuentralos.tecnosoft.dev/")
def encuentralos(query, qn, ctx):
    out = []
    ced = cedula_num(query) if es_cedula(query) else None
    tope = (ctx or {}).get("max_paginas", 50)
    for i in range(tope):
        r = http_get("https://encuentralos.tecnosoft.dev/api/personas",
                     params={"limit": 100, "offset": i * 100})
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])
        if not items:
            break
        for p in items:
            pc = limpiar_cedula(p.get("cedula"))
            blob = " ".join(str(p.get(k, "")) for k in
                            ("nombre", "cedula", "ultima_ubicacion", "descripcion"))
            if (ced and ced in pc) or coincide(qn, blob):
                out.append({"nombre": p.get("nombre"), "edad": p.get("edad"),
                            "cedula": p.get("cedula"), "estado": p.get("estado"),
                            "lugar": p.get("ultima_ubicacion") or p.get("pv_lugar"),
                            "url": "https://encuentralos.tecnosoft.dev/"})
        if i * 100 + len(items) >= data.get("total", 0):
            break
    return out

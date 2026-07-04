# -*- coding: utf-8 -*-
"""
app.py — servidor web local del buscador universal.

Sirve un frontend estático (carpeta web/) y expone la búsqueda por HTTP:

  GET /api/fuentes
      → catálogo de fuentes disponibles.

  GET /api/buscar?q=<texto>&fuentes=<a,b>&dtv_token=<t>&max_paginas=<n>
      → Server-Sent Events: emite un evento por fuente conforme responde,
        y un evento final {"fin": true}. Así la página muestra resultados
        de forma incremental sin esperar a la fuente más lenta.

Ejecutar:
    python app.py            # http://127.0.0.1:5000
    python app.py --port 8000 --host 0.0.0.0

Solo lectura: nunca escribe en las fuentes ni en base de datos alguna.
"""

import argparse
import json
from pathlib import Path

from flask import Flask, Response, request, send_from_directory

from buscador import FUENTES, buscar_stream
from buscador.registro import INDEXADAS_INDIRECTAMENTE

WEB_DIR = Path(__file__).parent / "web"

app = Flask(__name__, static_folder=None)


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/<path:archivo>")
def estaticos(archivo):
    return send_from_directory(WEB_DIR, archivo)


@app.get("/api/fuentes")
def api_fuentes():
    catalogo = [{
        "key": f.key, "label": f.label, "descripcion": f.descripcion,
        "grupo": f.grupo, "sitio": f.sitio, "requiere_token": f.requiere_token,
    } for f in FUENTES.values()]
    return {"fuentes": catalogo, "indirectas": INDEXADAS_INDIRECTAMENTE}


@app.get("/api/buscar")
def api_buscar():
    query = (request.args.get("q") or "").strip()
    if not query:
        return {"error": "falta el parámetro q"}, 400

    fuentes = request.args.get("fuentes") or None
    ctx = {
        "dtv_token": request.args.get("dtv_token") or None,
        "max_paginas": int(request.args.get("max_paginas") or 50),
    }

    def stream():
        for ev in buscar_stream(query, fuentes, ctx):
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'fin': True}, ensure_ascii=False)}\n\n"

    return Response(stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no"})


def main():
    ap = argparse.ArgumentParser(description="Servidor web del buscador universal")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    print(f"\n  Buscador Universal — Terremoto Venezuela 2026")
    print(f"  Abre en el navegador:  http://{args.host}:{args.port}\n")
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == "__main__":
    main()

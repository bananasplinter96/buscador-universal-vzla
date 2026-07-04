# -*- coding: utf-8 -*-
"""
cli.py — interfaz de línea de comandos del buscador universal.

Ejemplos:
    python cli.py "maria fernanda perez"
    python cli.py 12345678
    python cli.py "jose g" --fuentes tebusco,aquiestoyvenezuela
    python cli.py "ana diaz" --json
    python cli.py --listar-fuentes
    python cli.py "maria gonzalez" --dtv-token "TOKEN"   # incluye la de reCAPTCHA
"""

import argparse
import json
import sys

from buscador import FUENTES, buscar_stream


def main():
    ap = argparse.ArgumentParser(
        description="Buscador universal en vivo (solo lectura, no toca ninguna DB).")
    ap.add_argument("query", nargs="?", help="nombre (parcial) o cédula")
    ap.add_argument("--fuentes", default=None,
                    help="lista separada por comas (default: todas)")
    ap.add_argument("--max-paginas", type=int, default=50,
                    help="tope de páginas para fuentes grandes sin buscador (default 50)")
    ap.add_argument("--dtv-token", default=None,
                    help="token reCAPTCHA v3 para desaparecidos_terremoto (ver README)")
    ap.add_argument("--listar-fuentes", action="store_true", help="muestra el catálogo y sale")
    ap.add_argument("--json", action="store_true", help="salida en JSON")
    args = ap.parse_args()

    if args.listar_fuentes:
        print("Fuentes del buscador universal:\n")
        for f in FUENTES.values():
            marca = " [requiere --dtv-token]" if f.requiere_token else ""
            print(f"  {f.key:24s} {f.descripcion}{marca}")
        return

    if not args.query:
        ap.error("falta el argumento query (nombre o cédula)")

    ctx = {"max_paginas": args.max_paginas, "dtv_token": args.dtv_token}
    eventos = list(buscar_stream(args.query, args.fuentes, ctx))

    if args.json:
        salida = {"query": args.query, "resultados": {}, "errores": {}}
        for ev in eventos:
            if ev["error"]:
                salida["errores"][ev["fuente"]] = ev["error"]
            else:
                salida["resultados"][ev["fuente"]] = ev["resultados"]
        print(json.dumps(salida, ensure_ascii=False, indent=2))
        return

    total, con_error = 0, 0
    for ev in sorted(eventos, key=lambda e: e["fuente"]):
        print(f"\n=== {ev['fuente']} ({ev['label']}) ===")
        if ev["error"]:
            con_error += 1
            print(f"  [omitida/error] {ev['error']}")
            continue
        if not ev["resultados"]:
            print("  (sin coincidencias)")
            continue
        total += len(ev["resultados"])
        for h in ev["resultados"]:
            partes = [h.get("nombre") or "?"]
            for k in ("edad", "cedula", "estado", "lugar"):
                if h.get(k) not in (None, ""):
                    partes.append(f"{k}={h[k]}")
            print(f"  - {' | '.join(str(p) for p in partes)}")
            if h.get("url"):
                print(f"    {h['url']}")
    print(f"\nTotal coincidencias: {total}  "
          f"(fuentes: {len(eventos)}, con error/omitidas: {con_error})")


if __name__ == "__main__":
    sys.exit(main())

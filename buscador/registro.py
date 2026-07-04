"""
registro — catálogo de fuentes.

Cada fuente es una función `buscar(query, query_norm, ctx) -> list[dict]` que
devuelve una lista de coincidencias. Los diccionarios usan el esquema común:

    {
        "nombre":  str,
        "edad":    str | int | None,
        "cedula":  str | None,
        "estado":  str | None,   # buscado / localizado / a salvo / etc.
        "lugar":   str | None,
        "url":     str,          # a dónde ir para ver la ficha original
    }

El orquestador añade automáticamente la clave "fuente".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

# Grupos para la UI / documentación
GRUPO_NATIVO = "buscador nativo"     # el servidor filtra por ?q=
GRUPO_DUMP = "descarga + filtro"     # se baja el dataset y se filtra local


@dataclass
class Fuente:
    key: str
    label: str
    descripcion: str
    grupo: str
    sitio: str            # URL del sitio web público de la fuente
    requiere_token: bool
    fn: Callable


FUENTES: dict[str, Fuente] = {}


def registrar(key, label, descripcion, grupo, sitio="", requiere_token=False):
    """Decorador para registrar una función de búsqueda como fuente."""
    def deco(fn):
        FUENTES[key] = Fuente(
            key=key, label=label, descripcion=descripcion, grupo=grupo,
            sitio=sitio, requiere_token=requiere_token, fn=fn,
        )
        return fn
    return deco


# Plataformas que NO se consultan directamente pero cuya data llega a este
# buscador de forma indirecta (a través de los agregadores Hazlo Hoy y Yummy).
# Se listan en la interfaz para transparencia, con enlace a su sitio.
INDEXADAS_INDIRECTAMENTE = [
    {"nombre": "Venezuela Te Busca", "sitio": "https://venezuelatebusca.com/",
     "via": "vía Hazlo Hoy y Yummy · SOS"},
    {"nombre": "Terremoto Venezuela (.com)", "sitio": "https://terremotovenezuela.com/",
     "via": "vía Hazlo Hoy"},
    {"nombre": "Terremoto Venezuela (app)", "sitio": "https://terremotovenezuela.app/",
     "via": "vía Hazlo Hoy"},
    {"nombre": "Yummy · SOS (agregador federado)", "sitio": "https://sos.yummyrides.com/personas",
     "via": "cruza y deduplica varias listas"},
]


def claves() -> list[str]:
    return list(FUENTES)

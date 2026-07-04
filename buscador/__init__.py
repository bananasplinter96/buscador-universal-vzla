"""
Buscador Universal — Terremoto Venezuela 2026.

Paquete que consulta EN VIVO las plataformas ciudadanas de personas
desaparecidas/localizadas y unifica los resultados. Solo lectura: nunca
escribe en ninguna fuente ni en base de datos alguna.
"""

from .registro import FUENTES, Fuente
from .busqueda import buscar, buscar_stream
from . import fuentes as _fuentes  # noqa: F401  (registra las fuentes al importar)

__all__ = ["FUENTES", "Fuente", "buscar", "buscar_stream"]
__version__ = "1.0.0"

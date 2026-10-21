"""
engine/shared_assets.py

Los sonidos y la música comunes viven en `2027/assets/` (generados por
`herramientas/genlib.py`). Este módulo da rutas absolutas a esos archivos
desde cualquier juego, sin depender de dónde se ejecute.
"""

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # carpeta 2027


def sfx_path(name):
    """Ruta al efecto de sonido `name` (sin extensión)."""
    return os.path.join(_ROOT, "assets", "sonidos", f"{name}.wav")


def music_path(name):
    """Ruta a la música `name` (sin extensión)."""
    return os.path.join(_ROOT, "assets", "musica", f"{name}.wav")


def shared_dir():
    return os.path.join(_ROOT, "assets")

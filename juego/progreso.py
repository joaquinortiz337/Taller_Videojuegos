# juego/progreso.py
import json
import os

from juego import config as C
from juego.niveles import NIVELES, siguiente_nivel

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(RAIZ, C.ARCHIVO_PROGRESO)


def _vacio():
    return {"desbloqueados": [NIVELES[0]["id"]], "estrellas": {},
            "volumen_efectos": 0.7, "volumen_musica": 0.5}


class Progreso:
    """Guarda y carga el avance del jugador en progreso.json."""

    def __init__(self):
        self.datos = _vacio()
        self.cargar()

    def cargar(self):
        try:
            with open(RUTA, encoding="utf-8") as f:
                self.datos.update(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        if "volumen" in self.datos:   # archivos de versiones anteriores (un solo volumen)
            self.datos["volumen_efectos"] = self.datos.pop("volumen")

    def guardar(self):
        with open(RUTA, "w", encoding="utf-8") as f:
            json.dump(self.datos, f, indent=2, ensure_ascii=False)

    def borrar(self):
        efectos, musica = self.volumen_efectos, self.volumen_musica
        self.datos = _vacio()
        self.datos["volumen_efectos"] = efectos
        self.datos["volumen_musica"] = musica
        self.guardar()

    # ---- Consultas ----
    @property
    def volumen_efectos(self):
        return self.datos["volumen_efectos"]

    @volumen_efectos.setter
    def volumen_efectos(self, valor):
        self.datos["volumen_efectos"] = max(0.0, min(1.0, round(valor, 1)))
        self.guardar()

    @property
    def volumen_musica(self):
        return self.datos["volumen_musica"]

    @volumen_musica.setter
    def volumen_musica(self, valor):
        self.datos["volumen_musica"] = max(0.0, min(1.0, round(valor, 1)))
        self.guardar()

    def desbloqueado(self, id_nivel):
        return id_nivel in self.datos["desbloqueados"]

    def estrellas(self, id_nivel):
        """Devuelve dict(desempeno=0..3, dificil=bool, experto=bool)."""
        return self.datos["estrellas"].get(id_nivel, {"desempeno": 0, "dificil": False, "experto": False})

    def total_estrellas(self, id_nivel):
        e = self.estrellas(id_nivel)
        return e["desempeno"] + int(e["dificil"]) + int(e["experto"])

    # ---- Registrar una victoria ----
    def registrar_victoria(self, id_nivel, dificultad, desempeno):
        """Actualiza estrellas y desbloqueos. Devuelve el id del nivel recién desbloqueado (o None)."""
        e = dict(self.estrellas(id_nivel))
        e["desempeno"] = max(e["desempeno"], desempeno)
        if dificultad in ("dificil", "experto"):
            e["dificil"] = True          # ganar en Experto también cuenta como ganar en Difícil
        if dificultad == "experto":
            e["experto"] = True
        self.datos["estrellas"][id_nivel] = e

        nuevo = None
        sig = siguiente_nivel(id_nivel)
        if sig and sig not in self.datos["desbloqueados"]:
            self.datos["desbloqueados"].append(sig)
            nuevo = sig
        self.guardar()
        return nuevo

# juego/progreso.py
import json
import os

from juego import config as C
from juego.niveles import NIVELES, siguiente_nivel

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(RAIZ, C.ARCHIVO_PROGRESO)


def _vacio():
    return {"desbloqueados": [NIVELES[0]["id"]], "estrellas": {},
            "mejoras": dict(C.NIVELES_INICIALES),
            "volumen_efectos": 0.7, "volumen_musica": 0.5, "volumen_voz": 0.8}


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
        efectos, musica, voz = self.volumen_efectos, self.volumen_musica, self.volumen_voz
        self.datos = _vacio()
        self.datos["volumen_efectos"] = efectos
        self.datos["volumen_musica"] = musica
        self.datos["volumen_voz"] = voz
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

    @property
    def volumen_voz(self):
        return self.datos["volumen_voz"]

    @volumen_voz.setter
    def volumen_voz(self, valor):
        self.datos["volumen_voz"] = max(0.0, min(1.0, round(valor, 1)))
        self.guardar()

    def desbloqueado(self, id_nivel):
        return id_nivel in self.datos["desbloqueados"]

    def estrellas(self, id_nivel):
        """Devuelve dict(desempeno=0..3, dificil=bool, experto=bool)."""
        return self.datos["estrellas"].get(id_nivel, {"desempeno": 0, "dificil": False, "experto": False})

    def total_estrellas(self, id_nivel):
        e = self.estrellas(id_nivel)
        return e["desempeno"] + int(e["dificil"]) + int(e["experto"])

    # ---- Mejoras ----
    def nivel_poder(self, clave):
        return self.datos["mejoras"].get(clave, C.NIVELES_INICIALES[clave])

    def vidas_base(self):
        """Corazones de la base según la mejora comprada."""
        return C.MEJORA_BASE["niveles"][self.nivel_poder("base") - 1]["vidas"]

    def niveles_poderes(self):
        """Niveles con los que arrancan los poderes en la partida."""
        return {clave: self.nivel_poder(clave) for clave in C.ORDEN_PODERES}

    def estrellas_ganadas(self):
        return sum(self.total_estrellas(n["id"]) for n in NIVELES)

    def estrellas_gastadas(self):
        total = 0
        for clave in C.ORDEN_MEJORAS:
            for nivel in range(C.NIVELES_INICIALES[clave] + 1, self.nivel_poder(clave) + 1):
                total += C.COSTO_MEJORA[nivel]
        return total

    def estrellas_disponibles(self):
        return self.estrellas_ganadas() - self.estrellas_gastadas()

    def costo_mejora(self, clave):
        """Estrellas para subir un nivel ese poder, o None si ya está al máximo."""
        return C.COSTO_MEJORA.get(self.nivel_poder(clave) + 1)

    def mejorar(self, clave):
        """Sube un nivel el poder si alcanzan las estrellas. Devuelve True si se pudo."""
        costo = self.costo_mejora(clave)
        if costo is None or costo > self.estrellas_disponibles():
            return False
        self.datos["mejoras"][clave] = self.nivel_poder(clave) + 1
        self.guardar()
        return True

    def reiniciar_mejoras(self):
        """Devuelve todas las estrellas gastadas."""
        self.datos["mejoras"] = dict(C.NIVELES_INICIALES)
        self.guardar()

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

# juego/narrador.py
# Narrador: frases cortas en inglés según lo que pasa en la partida.
import random

from juego import config as C

# evento -> (archivos posibles en assets/sounds/voz, prioridad, segundos antes de poder repetirlo,
#            grupo de espera). Si hay varios archivos se elige uno al azar.
# Los eventos del mismo grupo comparten la espera (ej: los tres niveles de combo).
# Una frase de prioridad 3 o más corta a la que se esté diciendo.
FRASES = {
    "inicio":      (["defend_the_base"], 1, 999, "inicio"),
    "peligro":     (["danger", "watch_out"], 3, 12, "peligro"),
    "ultima_vida": (["last_chance"], 4, 999, "ultima_vida"),
    "combo_bajo":  (["nice", "good_job", "well_done"], 1, C.NARRADOR_ESPERA_COMBO, "combo"),        # 3-4
    "combo_medio": (["excellent", "great_combo", "amazing"], 2, C.NARRADOR_ESPERA_COMBO, "combo"),  # 5-7
    "combo_alto":  (["unstoppable", "incredible", "legendary"], 2, C.NARRADOR_ESPERA_COMBO, "combo"),  # 8+
    "armadura":    (["armor_down"], 1, 10, "armadura"),
    "ultimos":     (["final_wave"], 2, 999, "ultimos"),
    "jefe":        (["here_comes_the_boss"], 4, 999, "jefe"),
    "victoria":    (["victory"], 5, 999, "victoria"),
}


def evento_combo(combo):
    """Qué comentario corresponde a un combo de ese tamaño (None si es chico)."""
    if combo >= 8:
        return "combo_alto"
    if combo >= 5:
        return "combo_medio"
    if combo >= 3:
        return "combo_bajo"
    return None


class Narrador:
    def __init__(self, audio):
        self.audio = audio
        self.silencio = 0.0          # segundos que se queda callado después de una frase
        self.prioridad_actual = 0
        self.esperas = {}            # grupo -> segundos para poder repetirlo
        self.pendiente = None        # [segundos, evento]: frase que sale con un pequeño retraso
        self.ultimo_archivo = None

    def update(self, dt):
        self.silencio = max(0.0, self.silencio - dt)
        for grupo in list(self.esperas):
            self.esperas[grupo] -= dt
            if self.esperas[grupo] <= 0:
                del self.esperas[grupo]
        if self.pendiente:
            self.pendiente[0] -= dt
            if self.pendiente[0] <= 0:
                evento = self.pendiente[1]
                self.pendiente = None
                self.decir(evento)

    def decir(self, evento, retraso=0.0):
        """Dice la frase del evento (o la deja pendiente 'retraso' segundos)."""
        archivos, prioridad, espera, grupo = FRASES[evento]
        if grupo in self.esperas:
            return
        if retraso > 0:
            # Si ya había una pendiente, queda la más importante
            if not self.pendiente or FRASES[self.pendiente[1]][1] <= prioridad:
                self.pendiente = [retraso, evento]
            return
        hablando = self.silencio > 0 or self.audio.voz_sonando()
        if hablando and not (prioridad >= 3 and prioridad > self.prioridad_actual):
            return   # se descarta (no se acumulan frases viejas)
        # Solo frases que tengan su archivo de audio (si falta, ese evento queda en silencio)
        existentes = [a for a in archivos if self.audio.tiene_voz(a)]
        if not existentes:
            return
        opciones = [a for a in existentes if a != self.ultimo_archivo] or existentes
        archivo = random.choice(opciones)
        if self.audio.voz(archivo):
            self.ultimo_archivo = archivo
            self.prioridad_actual = prioridad
            self.silencio = C.NARRADOR_SILENCIO
            self.esperas[grupo] = espera

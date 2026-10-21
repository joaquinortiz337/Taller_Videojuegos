# juego/sonido.py
import os
import pygame

from engine.audio import AudioManager  # Hereda del motor

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_SONIDOS = os.path.join(RAIZ, "assets", "sounds")
CARPETA_MUSICA = os.path.join(RAIZ, "assets", "music")


class Sonidos(AudioManager):
    """
    El AudioManager del motor + lo que necesitamos:
      - volumen separado para efectos y música,
      - limitar un mismo sonido si se dispara muchas veces seguidas,
      - sonidos en bucle (mecha, agujero negro) que se pueden pausar/cortar,
      - música por nombre: si existe assets/music/<nombre>.(ogg|mp3|wav) suena; si no, nada.
    """
    ESPERA_MINIMA = 0.05   # segundos mínimos entre dos reproducciones del mismo sonido

    def __init__(self):
        super().__init__(num_channels=24)
        self.volumen_efectos = 0.7
        self.volumen_musica = 0.5
        self._ultimo = {}
        self.musica_actual = None
        if self.enabled and os.path.isdir(CARPETA_SONIDOS):
            for archivo in os.listdir(CARPETA_SONIDOS):
                if archivo.endswith(".wav"):
                    self.load_sound(archivo[:-4], os.path.join(CARPETA_SONIDOS, archivo))

    # ---------- Volumen ----------
    def set_volumenes(self, efectos, musica):
        self.volumen_efectos = efectos
        self.volumen_musica = musica
        if not self.enabled:
            return
        for s in self.sounds.values():
            s.set_volume(efectos)
        pygame.mixer.music.set_volume(musica)

    # ---------- Efectos ----------
    def reproducir(self, nombre, volumen=1.0, bucle=False):
        """Reproduce un efecto. Devuelve el canal (útil para cortar un bucle) o None."""
        if not self.enabled or nombre not in self.sounds:
            return None
        ahora = pygame.time.get_ticks() / 1000
        if not bucle and ahora - self._ultimo.get(nombre, -1) < self.ESPERA_MINIMA:
            return None   # se disparó hace muy poco: no se apila
        self._ultimo[nombre] = ahora
        canal = pygame.mixer.find_channel()
        if canal:
            canal.play(self.sounds[nombre], loops=-1 if bucle else 0)
            canal.set_volume(max(0.0, min(1.0, volumen)))
        return canal

    # ---------- Música ----------
    def musica(self, nombre):
        """Pone la música 'nombre' si existe el archivo (y si no es la que ya suena)."""
        if not self.enabled or nombre == self.musica_actual:
            return
        for ext in (".ogg", ".mp3", ".wav"):
            ruta = os.path.join(CARPETA_MUSICA, nombre + ext)
            if os.path.exists(ruta):
                self.load_music(ruta)
                self.play_music(volume=self.volumen_musica)
                self.musica_actual = nombre
                return
        # No hay archivo para esta música: se corta la anterior
        self.stop_music()
        self.musica_actual = None

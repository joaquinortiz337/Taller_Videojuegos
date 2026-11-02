# juego/sonido.py
import os
import pygame

from engine.audio import AudioManager  # Hereda del motor

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_SONIDOS = os.path.join(RAIZ, "assets", "sounds")
CARPETA_VOZ = os.path.join(CARPETA_SONIDOS, "voz")
CARPETA_MUSICA = os.path.join(RAIZ, "assets", "music")

# Música de la partida en capas: suenan las tres a la vez y solo cambia el volumen de cada una
CAPAS = ("base", "tension", "percusion")   # archivos assets/music/partida_<capa>.(ogg|wav)
VELOCIDAD_MEZCLA = 1.2   # cuánto cambia por segundo el volumen de una capa (0 a 1)
VELOCIDAD_AGACHE = 3.0   # qué tan rápido baja/sube la música cuando habla el narrador


def _buscar(carpeta, nombre):
    for ext in (".ogg", ".mp3", ".wav"):
        ruta = os.path.join(carpeta, nombre + ext)
        if os.path.exists(ruta):
            return ruta
    return None


class Sonidos(AudioManager):
    """
    El AudioManager del motor + lo que necesitamos:
      - volumen separado para efectos, música y voz del narrador,
      - limitar un mismo sonido si se dispara muchas veces seguidas,
      - sonidos en bucle (mecha, agujero negro) que se pueden pausar/cortar,
      - música por nombre: si existe assets/music/<nombre>.(ogg|mp3|wav) suena; si no, nada,
      - música de la partida en capas (base, tensión, percusión) que se mezclan según el peligro,
      - un canal propio para el narrador (una frase a la vez).
    Canales reservados: 0, 1 y 2 para las capas de música, 3 para el narrador.
    """
    ESPERA_MINIMA = 0.05   # segundos mínimos entre dos reproducciones del mismo sonido

    def __init__(self):
        super().__init__(num_channels=24)
        self.volumen_efectos = 0.7
        self.volumen_musica = 0.5
        self.volumen_voz = 0.8
        self._ultimo = {}
        self.musica_actual = None
        self.capas = {}
        self.mezcla = {"base": 1.0, "tension": 0.0, "percusion": 0.0}       # volumen actual
        self.mezcla_objetivo = dict(self.mezcla)                              # hacia dónde va
        self.agache = 1.0            # la música baja mientras habla el narrador
        self.agache_voz = 0.55
        if not self.enabled:
            return
        if os.path.isdir(CARPETA_SONIDOS):
            for archivo in os.listdir(CARPETA_SONIDOS):
                if archivo.endswith(".wav"):
                    self.load_sound(archivo[:-4], os.path.join(CARPETA_SONIDOS, archivo))
        if os.path.isdir(CARPETA_VOZ):
            for archivo in os.listdir(CARPETA_VOZ):
                if archivo.endswith((".wav", ".ogg")):
                    self.load_sound("voz_" + archivo[:-4], os.path.join(CARPETA_VOZ, archivo))
        for capa in CAPAS:
            ruta = _buscar(CARPETA_MUSICA, "partida_" + capa)
            if ruta:
                self.capas[capa] = pygame.mixer.Sound(ruta)
        pygame.mixer.set_reserved(4)
        self.canales_capas = {capa: pygame.mixer.Channel(i) for i, capa in enumerate(CAPAS)}
        self.canal_voz = pygame.mixer.Channel(3)

    # ---------- Volumen ----------
    def set_volumenes(self, efectos, musica, voz=None):
        self.volumen_efectos = efectos
        self.volumen_musica = musica
        if voz is not None:
            self.volumen_voz = voz
        if not self.enabled:
            return
        for nombre, s in self.sounds.items():
            s.set_volume(self.volumen_voz if nombre.startswith("voz_") else efectos)
        pygame.mixer.music.set_volume(musica)
        self._aplicar_mezcla()

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

    # ---------- Narrador ----------
    def voz(self, nombre):
        """Dice la frase assets/sounds/voz/<nombre> (corta la que estuviera diciendo)."""
        clave = "voz_" + nombre
        if not self.enabled or clave not in self.sounds:
            return False
        self.canal_voz.play(self.sounds[clave])
        return True

    def tiene_voz(self, nombre):
        """True si existe assets/sounds/voz/<nombre>.(wav|ogg)."""
        return ("voz_" + nombre) in self.sounds

    def voz_sonando(self):
        return self.enabled and self.canal_voz.get_busy()

    # ---------- Música ----------
    def musica(self, nombre):
        """Pone la música 'nombre' si existe el archivo (y si no es la que ya suena).
        'partida' usa las capas si están las tres; si no, busca partida.(ogg|mp3|wav)."""
        if not self.enabled or nombre == self.musica_actual:
            return
        if nombre == "partida" and len(self.capas) == len(CAPAS):
            self.stop_music()
            self.mezcla = {"base": 1.0, "tension": 0.0, "percusion": 0.0}
            self.mezcla_objetivo = dict(self.mezcla)
            for capa in CAPAS:   # arrancan juntas en el mismo instante: quedan sincronizadas
                self.canales_capas[capa].play(self.capas[capa], loops=-1)
            self._aplicar_mezcla()
            self.musica_actual = nombre
            return
        self._parar_capas()
        ruta = _buscar(CARPETA_MUSICA, nombre)
        if ruta:
            self.load_music(ruta)
            self.play_music(volume=self.volumen_musica)
            self.musica_actual = nombre
            return
        # No hay archivo para esta música: se corta la anterior
        self.stop_music()
        self.musica_actual = None

    def _parar_capas(self):
        if self.enabled and self.capas:
            for canal in self.canales_capas.values():
                canal.stop()

    def mezclar_musica(self, tension, percusion):
        """Volumen deseado (0 a 1) de las capas de tensión y percusión; cambia de a poco."""
        self.mezcla_objetivo["tension"] = max(0.0, min(1.0, tension))
        self.mezcla_objetivo["percusion"] = max(0.0, min(1.0, percusion))

    def actualizar_musica(self, dt):
        if not self.enabled or self.musica_actual != "partida" or not self.capas:
            return
        objetivo = self.agache_voz if self.voz_sonando() else 1.0
        paso = VELOCIDAD_AGACHE * dt
        self.agache = min(objetivo, self.agache + paso) if objetivo > self.agache else max(objetivo, self.agache - paso)
        paso = VELOCIDAD_MEZCLA * dt
        for capa, objetivo in self.mezcla_objetivo.items():
            actual = self.mezcla[capa]
            self.mezcla[capa] = min(objetivo, actual + paso) if objetivo > actual else max(objetivo, actual - paso)
        self._aplicar_mezcla()

    def _aplicar_mezcla(self):
        if not self.enabled or not self.capas or self.musica_actual != "partida":
            return
        for capa, canal in self.canales_capas.items():
            canal.set_volume(self.volumen_musica * self.mezcla[capa] * self.agache)

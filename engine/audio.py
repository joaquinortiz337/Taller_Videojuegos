"""
engine/audio.py

Gestor de audio: música de fondo y efectos de sonido.
Si el sistema no tiene audio, el gestor queda desactivado pero el juego
sigue funcionando.
"""

import pygame


class AudioManager:
    """Carga y reproduce música y efectos de sonido."""

    def __init__(self, num_channels=16):
        self.sounds = {}
        self.music_path = None
        self.enabled = True
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(num_channels)
            print("AudioManager inicializado correctamente.")
        except pygame.error as e:
            print(f"Error al inicializar AudioManager: {e}. El audio estará desactivado.")
            self.enabled = False
            self.sounds = None

    # ------------------------------- Efectos ------------------------------ #
    def load_sound(self, name, path):
        """Carga un efecto de sonido y lo asocia a un nombre clave."""
        if not self.enabled:
            return
        try:
            self.sounds[name] = pygame.mixer.Sound(path)
        except pygame.error as e:
            print(f"Error al cargar el sonido '{name}' desde '{path}': {e}")

    def play_sound(self, name, loops=0):
        """Reproduce un efecto de sonido en el primer canal libre."""
        if not self.enabled or name not in self.sounds:
            return
        channel = pygame.mixer.find_channel()
        if channel:
            channel.play(self.sounds[name], loops)

    # -------------------------------- Música ------------------------------ #
    def load_music(self, path):
        """Deja preparada la ruta de la música de fondo."""
        if not self.enabled:
            return
        self.music_path = path

    def play_music(self, loops=-1, volume=0.5):
        """Reproduce la música de fondo en bucle."""
        if not self.enabled or not self.music_path:
            return
        try:
            pygame.mixer.music.load(self.music_path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops)
        except pygame.error as e:
            print(f"Error al reproducir la música desde '{self.music_path}': {e}")

    def stop_music(self):
        if not self.enabled:
            return
        pygame.mixer.music.stop()

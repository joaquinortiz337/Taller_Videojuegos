"""
engine/background.py

Fondos dinámicos:

- ParallaxBackground: varias capas que se desplazan a distinta velocidad.
- FrameBackground: reproduce una secuencia de imágenes (un "vídeo" exportado
  a frames), sin necesitar librerías externas.
- VideoBackground: vídeo en tiempo real con OpenCV (opcional; si no está
  instalado, se desactiva solo).
"""

import os

import pygame


class ParallaxLayer:
    def __init__(self, image, speed, y=0, repeat_x=True):
        self.image = image
        self.speed = speed
        self.y = y
        self.repeat_x = repeat_x
        self.offset = 0.0

    def update(self, dx):
        self.offset = (self.offset + dx * self.speed) % self.image.get_width()

    def draw(self, surface):
        w = self.image.get_width()
        x = -self.offset
        surface.blit(self.image, (x, self.y))
        if self.repeat_x:
            surface.blit(self.image, (x + w, self.y))


class ParallaxBackground:
    """Conjunto de capas ordenadas de la más lejana a la más cercana."""

    def __init__(self):
        self.layers = []

    def add_layer(self, image, speed, y=0, repeat_x=True):
        self.layers.append(ParallaxLayer(image, speed, y, repeat_x))

    def update(self, dx):
        for layer in self.layers:
            layer.update(dx)

    def draw(self, surface):
        for layer in self.layers:
            layer.draw(surface)


class FrameBackground:
    """Reproduce una carpeta de imágenes (frame_00000.png, frame_00001.png...)."""

    def __init__(self, frames_dir, fps=20):
        self.frames = []
        for name in sorted(os.listdir(frames_dir)):
            if name.lower().endswith((".png", ".jpg", ".bmp")):
                self.frames.append(
                    pygame.image.load(os.path.join(frames_dir, name)).convert()
                )
        self.fps = fps
        self.index = 0
        self.timer = 0.0

    def update(self, dt):
        if not self.frames:
            return
        self.timer += dt
        if self.timer >= 1.0 / self.fps:
            self.timer = 0.0
            self.index = (self.index + 1) % len(self.frames)

    def draw(self, surface):
        if self.frames:
            surface.blit(self.frames[self.index], (0, 0))

    def __len__(self):
        return len(self.frames)


class VideoBackground:
    """
    Fondo de vídeo en tiempo real con OpenCV.

    Si no está instalado `opencv-python`, el objeto queda inactivo y el juego
    puede seguir funcionando con otro fondo.
    """

    def __init__(self, video_path, size=None):
        self.available = False
        self.capture = None
        try:
            import cv2  # noqa: F401
            self._cv2 = cv2
            self.capture = cv2.VideoCapture(video_path)
            self.available = self.capture.isOpened()
        except Exception as e:
            print(f"VideoBackground desactivado (falta OpenCV o el vídeo): {e}")

        self.size = size
        self.surface = None

    def update(self, dt):
        if not self.available:
            return
        ok, frame = self.capture.read()
        if not ok:
            self.capture.set(self._cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self.capture.read()
        if not ok:
            return
        frame = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
        surf = pygame.image.frombuffer(frame.tobytes(),
                                       frame.shape[1::-1], "RGB")
        if self.size:
            surf = pygame.transform.scale(surf, self.size)
        self.surface = surf

    def draw(self, surface):
        if self.surface:
            surface.blit(self.surface, (0, 0))

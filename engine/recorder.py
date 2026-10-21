"""
engine/recorder.py

Graba la pantalla del juego como una secuencia de PNG y, si está disponible
FFmpeg, la convierte en vídeo (mp4).

Uso típico (clase 14):
    rec = Recorder("salida", fps=30)
    ...
    rec.capture(self.screen)      # cada frame mientras se graba
    rec.export("animacion.mp4")   # al terminar
"""

import os
import shutil
import subprocess

import pygame


class Recorder:
    def __init__(self, output_dir, fps=30):
        self.output_dir = output_dir
        self.fps = fps
        self.frame = 0
        self.frames_dir = os.path.join(output_dir, "frames")
        os.makedirs(self.frames_dir, exist_ok=True)

    def capture(self, surface):
        """Guarda el frame actual. Devuelve la ruta del PNG."""
        path = os.path.join(self.frames_dir, f"frame_{self.frame:05d}.png")
        pygame.image.save(surface, path)
        self.frame += 1
        return path

    def clear(self):
        """Borra los frames grabados y reinicia el contador."""
        for name in os.listdir(self.frames_dir):
            os.remove(os.path.join(self.frames_dir, name))
        self.frame = 0

    def export(self, filename="video.mp4", fps=None, keep_frames=False):
        """Convierte los frames en vídeo con FFmpeg. Devuelve la ruta o None."""
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            print("FFmpeg no está instalado o no está en el PATH: se conservan los PNG.")
            return None

        output_path = os.path.join(self.output_dir, filename)
        cmd = [
            ffmpeg, "-y",
            "-framerate", str(fps or self.fps),
            "-i", os.path.join(self.frames_dir, "frame_%05d.png"),
            "-pix_fmt", "yuv420p",
            output_path,
        ]
        try:
            subprocess.run(cmd, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Vídeo exportado en '{output_path}'")
        except subprocess.CalledProcessError as e:
            print(f"Error al exportar el vídeo: {e}")
            return None

        if not keep_frames:
            self.clear()
        return output_path

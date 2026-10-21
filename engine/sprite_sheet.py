"""
engine/sprite_sheet.py

Lee un JSON generado por el editor de spritesheets del curso y permite
recortar sprites sueltos o animaciones completas de la imagen.

El JSON tiene esta forma (resumida):

    {
      "spritesheet_path": "ruta/imagen.png",
      "animations": {
        "idle":        [ {"name": "...", "x": 0, "y": 0, "width": 32, "height": 32}, ... ],
        "walk_right":  [ ... ]
      }
    }

La imagen se busca SIEMPRE junto al JSON (usando solo el nombre de archivo),
para que el proyecto funcione aunque se mueva de carpeta o de equipo.
"""

import os
import json

import pygame


class Spritesheet:
    """Carga y gestiona una spritesheet descrita por un JSON."""

    def __init__(self, json_path):
        with open(json_path, encoding="utf-8") as f:
            self.data = json.load(f)

        # Nos quedamos solo con el nombre de archivo y lo buscamos junto al JSON.
        spritesheet_filename = os.path.basename(self.data["spritesheet_path"])
        json_dir = os.path.dirname(json_path)
        full_image_path = os.path.join(json_dir, spritesheet_filename)

        self.spritesheet = pygame.image.load(full_image_path).convert_alpha()

    def get_sprite(self, name):
        """Devuelve una Surface a partir del nombre del sprite."""
        for anim_list in self.data["animations"].values():
            for sprite_data in anim_list:
                if sprite_data["name"] == name:
                    rect = pygame.Rect(
                        sprite_data["x"],
                        sprite_data["y"],
                        sprite_data["width"],
                        sprite_data["height"],
                    )
                    return self.spritesheet.subsurface(rect)
        raise ValueError(f"Sprite con nombre '{name}' no encontrado en el JSON.")

    def get_animation_frames(self, anim_name):
        """Devuelve la lista de Surfaces (frames) de una animación."""
        if anim_name not in self.data["animations"]:
            raise ValueError(f"Animación '{anim_name}' no encontrada en el JSON.")

        frames = []
        for sprite_data in self.data["animations"][anim_name]:
            rect = pygame.Rect(
                sprite_data["x"],
                sprite_data["y"],
                sprite_data["width"],
                sprite_data["height"],
            )
            frames.append(self.spritesheet.subsurface(rect))
        return frames

    def sprite_names(self):
        """Devuelve todos los nombres de sprite disponibles (útil para depurar)."""
        return sorted(
            sprite["name"]
            for anim_list in self.data["animations"].values()
            for sprite in anim_list
        )

"""
engine/asset_manager.py

Gestor centralizado de recursos gráficos (y punto de acceso a sonidos).
Carga cada recurso UNA vez y lo sirve por un nombre clave.
"""

import pygame

from engine.sprite_sheet import Spritesheet


class AssetManager:
    def __init__(self):
        self.spritesheets = {}
        self.images = {}
        self.sounds = {}

    # ---------------------------- Spritesheets ---------------------------- #
    def load_spritesheet(self, name, json_path):
        """Carga un spritesheet desde un JSON y lo guarda con un nombre clave."""
        try:
            self.spritesheets[name] = Spritesheet(json_path)
            print(f"Spritesheet '{name}' cargado desde '{json_path}'")
        except Exception as e:
            print(f"Error al cargar el spritesheet '{name}': {e}")
            raise

    def get_sprite(self, sheet_name, sprite_name):
        """Obtiene un sprite concreto de un spritesheet ya cargado."""
        if sheet_name not in self.spritesheets:
            raise KeyError(f"No se ha cargado un spritesheet con el nombre '{sheet_name}'")
        return self.spritesheets[sheet_name].get_sprite(sprite_name)

    def get_animation(self, sheet_name, anim_name):
        """Obtiene los frames de una animación de un spritesheet ya cargado."""
        if sheet_name not in self.spritesheets:
            raise KeyError(f"No se ha cargado un spritesheet con el nombre '{sheet_name}'")
        return self.spritesheets[sheet_name].get_animation_frames(anim_name)

    # ------------------------------- Imágenes ----------------------------- #
    def load_image(self, name, image_path):
        """Carga una imagen suelta y la guarda con un nombre clave."""
        try:
            self.images[name] = pygame.image.load(image_path).convert_alpha()
            print(f"Imagen '{name}' cargada desde '{image_path}'")
        except Exception as e:
            print(f"Error al cargar la imagen '{name}': {e}")
            raise

    def get_image(self, name):
        """Obtiene una imagen suelta ya cargada."""
        if name not in self.images:
            raise KeyError(f"No se ha cargado una imagen con el nombre '{name}'")
        return self.images[name]

"""
engine/tilemap.py

Carga niveles creados en Tiled (.json + .tsx/.png) y los convierte en
grupos de sprites listos para el juego.

Devuelve:
    sprite_groups, world_width, world_height, player_start_pos

donde `sprite_groups` es un diccionario con:
    "all_sprites"      -> todos los tiles
    "collision_sprites"-> solo los tiles que colisionan
    "enemies"          -> marcadores de spawn de enemigos (objetos)
    "powerups"         -> marcadores de spawn de power-ups (objetos)

Además, los marcadores de spawn se exponen también como lista en
`sprite_groups["spawns"]` por comodidad.

Es tolerante con los nombres usados en los distintos ejemplos del curso:
acepta `player_start` o `start_point` para la posición inicial del jugador.
"""

import os
import json
import xml.etree.ElementTree as ET

import pygame

from .game_object import GameObject


class Tile(GameObject):
    """Un tile estático del mapa, posicionado por su esquina superior izquierda."""

    def __init__(self, x, y, image):
        super().__init__(x, y, image)
        self.rect = self.image.get_rect(topleft=(x, y))


class Spawn(pygame.sprite.Sprite):
    """Marcador invisible creado a partir de un objeto de Tiled."""

    def __init__(self, x, y, kind, properties=None):
        super().__init__()
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.kind = kind
        self.properties = properties or {}


def _as_bool(value):
    return str(value).lower() in ("true", "1", "yes")


class TilemapLoader:
    def __init__(self, assets_manager):
        self.assets = assets_manager

    def load_level(self, level_json_path):
        try:
            with open(level_json_path, encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error fatal al cargar o leer el archivo de nivel: {e}")
            return None, 0, 0, (150, 150)

        tile_width = data["tilewidth"]
        tile_height = data["tileheight"]
        json_dir = os.path.dirname(level_json_path)

        # --- 1. Tileset (imagen + propiedades de tiles) --- #
        tileset_info = data["tilesets"][0]
        first_gid = tileset_info["firstgid"]
        tileset_image_filename = ""
        tile_properties = {}

        if "source" in tileset_info:
            tsx_path = os.path.join(json_dir, tileset_info["source"])
            try:
                root = ET.parse(tsx_path).getroot()
                tileset_image_filename = root.find("image").get("source")
                for tile_node in root.findall("tile"):
                    tile_id = int(tile_node.get("id"))
                    props_node = tile_node.find("properties")
                    if props_node is not None:
                        tile_properties[tile_id] = {}
                        for prop_node in props_node.findall("property"):
                            name = prop_node.get("name")
                            value = prop_node.get("value")
                            if prop_node.get("type") == "bool":
                                value = _as_bool(value)
                            tile_properties[tile_id][name] = value
            except Exception as e:
                print(f"Error al leer el archivo .tsx en '{tsx_path}': {e}")
                return None, 0, 0, (150, 150)
        elif "image" in tileset_info:
            tileset_image_filename = tileset_info["image"]

        if not tileset_image_filename:
            print("Error: no se encontró la imagen del tileset.")
            return None, 0, 0, (150, 150)

        tileset_image_path = os.path.join(json_dir, tileset_image_filename)
        tileset_name = os.path.basename(tileset_image_path)
        self.assets.load_image(tileset_name, tileset_image_path)
        tileset_img = self.assets.get_image(tileset_name)

        tiles = {}
        gid = first_gid
        for y in range(0, tileset_img.get_height(), tile_height):
            for x in range(0, tileset_img.get_width(), tile_width):
                if (x + tile_width <= tileset_img.get_width()
                        and y + tile_height <= tileset_img.get_height()):
                    tiles[gid] = tileset_img.subsurface((x, y, tile_width, tile_height))
                    gid += 1

        # --- 2. Capas --- #
        world_width = data["width"] * tile_width
        world_height = data["height"] * tile_height

        sprite_groups = {
            "all_sprites": pygame.sprite.Group(),
            "collision_sprites": pygame.sprite.Group(),
            "enemies": pygame.sprite.Group(),
            "powerups": pygame.sprite.Group(),
        }
        spawns = []
        player_start_pos = (150, 150)  # posición por defecto a prueba de fallos

        for layer in data["layers"]:
            if layer["type"] == "tilelayer" and "data" in layer:
                layer_collides = False
                for prop in layer.get("properties", []):
                    if prop.get("name") == "collide" and _as_bool(prop.get("value")):
                        layer_collides = True

                for i, gid_val in enumerate(layer["data"]):
                    if gid_val == 0 or gid_val not in tiles:
                        continue

                    pos_x = (i % data["width"]) * tile_width
                    pos_y = (i // data["width"]) * tile_height

                    tile_sprite = Tile(pos_x, pos_y, tiles[gid_val])
                    sprite_groups["all_sprites"].add(tile_sprite)

                    tile_id_in_tileset = gid_val - first_gid
                    props = tile_properties.get(tile_id_in_tileset, {})
                    tile_collides = _as_bool(props.get("collides", props.get("collide", False)))
                    if layer_collides or tile_collides:
                        sprite_groups["collision_sprites"].add(tile_sprite)

            elif layer["type"] == "objectgroup":
                for obj in layer.get("objects", []):
                    self._process_object(obj, sprite_groups, spawns)
                    if obj.get("name") in ("player_start", "start_point"):
                        player_start_pos = (obj["x"], obj["y"])

        sprite_groups["spawns"] = spawns
        return sprite_groups, world_width, world_height, player_start_pos

    # ------------------------------------------------------------------ #
    @staticmethod
    def _process_object(obj, sprite_groups, spawns):
        """Clasifica un objeto de Tiled como enemigo, power-up o ignorado."""
        label = f"{obj.get('name', '')} {obj.get('type', '')}".lower()
        kind = None
        if "enem" in label:
            kind = "enemy"
        elif "power" in label or "potion" in label or "vida" in label or "coin" in label:
            kind = "powerup"

        if kind is None:
            return

        props = {p.get("name"): p.get("value") for p in obj.get("properties", [])}
        spawn = Spawn(obj["x"], obj["y"], kind, props)
        spawns.append(spawn)
        sprite_groups["enemies" if kind == "enemy" else "powerups"].add(spawn)

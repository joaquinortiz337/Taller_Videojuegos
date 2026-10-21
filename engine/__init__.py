"""
Motor 2D del curso de Videojuegos (versión 2027).

El motor soporta DOS enfoques de trabajo:

1) Enfoque Game Loop (herencia):
   Heredar de `GameLoop` y sobrescribir:
       handle_specific_events(event)
       update_game_logic()
       draw_game_elements()
   Ideal para demos y juegos con un único "estado" (por ejemplo el sandbox
   de físicas o el primer Arkanoid).

2) Enfoque Game Scenes (gestor de escenas):
   Heredar de `Game` (que ya es un `GameLoop`) y registrar escenas con
   `add_scene(nombre, clase_de_escena)` y cambiar con `change_scene(nombre)`.
   Cada escena hereda de `Scene` y sobrescribe:
       handle_events(events)
       update()
       draw(surface)
   Ideal para juegos con menú, juego, game over, pausa, niveles, etc.

Ambos enfoques comparten exactamente el mismo bucle y los mismos módulos
(assets, spritesheets, audio, físicas, tilemaps, cámara, UI).
"""

from engine.game_loop import GameLoop, Game
from engine.ui import Scene, Button
from engine.game_object import GameObject
from engine.sprite_sheet import Spritesheet
from engine.asset_manager import AssetManager
from engine.tilemap import TilemapLoader, Tile
from engine.camera import Camera
from engine.dialogue_manager import DialogueManager

# Módulos de las clases 13 a 26.
from engine.iso_tools import grid_to_iso, iso_to_grid, IsoSprite, sort_by_depth
from engine.timeline import Timeline
from engine.recorder import Recorder
from engine.particle import Particle, ParticleSystem
from engine.background import ParallaxBackground, FrameBackground, VideoBackground
from engine.hotspot import Hotspot
from engine.inventory import Inventory, Item
from engine.cursor import Cursor
from engine.dialogue import DialogueBox, DialogueNode
from engine.challenge import Challenge
from engine.ui_elements import Label, Panel, ProgressBar, HealthBar

# El audio y las físicas dependen de librerías/entornos concretos.
# Los importamos de forma tolerante para que el motor siga siendo utilizable
# aunque no haya tarjeta de sonido o no esté instalado pymunk.
try:
    from engine.audio import AudioManager
except Exception:  # pragma: no cover
    AudioManager = None

try:
    from engine.physics import PhysicsMixin
except Exception:  # pragma: no cover
    PhysicsMixin = None

try:
    from engine.physics_object import PhysicsObject, add_walls, add_static_segment
except Exception:  # pragma: no cover
    PhysicsObject = None
    add_walls = None
    add_static_segment = None

__all__ = [
    "GameLoop",
    "Game",
    "Scene",
    "Button",
    "GameObject",
    "Spritesheet",
    "AssetManager",
    "TilemapLoader",
    "Tile",
    "Camera",
    "DialogueManager",
    "grid_to_iso",
    "iso_to_grid",
    "IsoSprite",
    "sort_by_depth",
    "Timeline",
    "Recorder",
    "Particle",
    "ParticleSystem",
    "ParallaxBackground",
    "FrameBackground",
    "VideoBackground",
    "Hotspot",
    "Inventory",
    "Item",
    "Cursor",
    "DialogueBox",
    "DialogueNode",
    "Challenge",
    "Label",
    "Panel",
    "ProgressBar",
    "HealthBar",
    "AudioManager",
    "PhysicsMixin",
    "PhysicsObject",
    "add_walls",
    "add_static_segment",
]

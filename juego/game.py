# juego/game.py
import os
import pygame

from engine.game_loop import Game              # Hereda del motor (GameLoop + gestor de escenas)
from engine.asset_manager import AssetManager  # Usa el motor
from juego import config as C
from juego.progreso import Progreso
from juego.sonido import Sonidos
from juego.scenes.menu_scene import MenuScene
from juego.scenes.opciones_scene import OpcionesScene
from juego.scenes.controles_scene import ControlesScene
from juego.scenes.seleccion_scene import SeleccionScene
from juego.scenes.nivel_scene import NivelScene
from juego.scenes.game_scene import GameScene
from juego.scenes.end_scenes import GameOverScene, VictoryScene

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(RAIZ, "assets")


class FisicasGame(Game):
    """
    Clase principal. Hereda de Game (motor del curso), que ya trae el bucle
    principal y el gestor de escenas: add_scene() registra cada escena y
    change_scene() cambia de escena de forma segura al empezar el siguiente frame.
    """

    def __init__(self):
        super().__init__(C.ANCHO, C.ALTO, C.TITULO, C.FPS)
        self.assets = AssetManager()
        self.audio = Sonidos()                      # todos los efectos de assets/sounds
        self.assets.sounds = self.audio.sounds or {}  # el AssetManager comparte los mismos sonidos
        self.progreso = Progreso()
        self.aplicar_volumen()

        self.add_scene("menu", MenuScene)          # menú principal
        self.add_scene("opciones", OpcionesScene)
        self.add_scene("controles", ControlesScene)
        self.add_scene("niveles", SeleccionScene)  # selección de niveles
        self.add_scene("nivel", NivelScene)        # nivel seleccionado (dificultad, estrellas)
        self.add_scene("juego", GameScene)
        self.add_scene("game_over", GameOverScene)
        self.add_scene("victoria", VictoryScene)
        self.change_scene("menu")

    def aplicar_volumen(self):
        self.audio.set_volumenes(self.progreso.volumen_efectos, self.progreso.volumen_musica)

    def salir(self):
        self.running = False

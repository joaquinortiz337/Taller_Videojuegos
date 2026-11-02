# juego/game.py
from engine.game_loop import Game              # Hereda del motor (GameLoop + gestor de escenas)
from engine.asset_manager import AssetManager  # Usa el motor
from juego import config as C
from juego.progreso import Progreso
from juego.estilo import FondoMenu
from juego.sonido import Sonidos
from juego.scenes.menu_scene import MenuScene
from juego.scenes.opciones_scene import OpcionesScene
from juego.scenes.controles_scene import ControlesScene
from juego.scenes.seleccion_scene import SeleccionScene
from juego.scenes.mejoras_scene import MejorasScene
from juego.scenes.creditos_scene import CreditosScene
from juego.scenes.nivel_scene import NivelScene
from juego.scenes.game_scene import GameScene
from juego.scenes.end_scenes import GameOverScene, VictoryScene

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
        self.fondo_menu = FondoMenu()   # fondo animado compartido por todas las pantallas de menú
        self._foto = None               # última imagen de la pantalla anterior (fundido)
        self._fundido = 0.0

        self.add_scene("menu", MenuScene)          # menú principal
        self.add_scene("opciones", OpcionesScene)
        self.add_scene("controles", ControlesScene)
        self.add_scene("niveles", SeleccionScene)  # selección de niveles
        self.add_scene("nivel", NivelScene)        # nivel seleccionado (dificultad, estrellas)
        self.add_scene("mejoras", MejorasScene)    # gastar estrellas en mejorar los poderes
        self.add_scene("juego", GameScene)
        self.add_scene("game_over", GameOverScene)
        self.add_scene("victoria", VictoryScene)
        self.add_scene("creditos", CreditosScene)
        self.change_scene("menu")

    # --- Fundido entre pantallas ---
    def _apply_pending_scene(self):
        if self._pending_scene is not None and self.current_scene is not None:
            self._foto = self.screen.copy()    # cómo se veía la pantalla que se va
            self._fundido = C.FUNDIDO
        super()._apply_pending_scene()

    def update_game_logic(self):
        super().update_game_logic()
        dt = 1 / C.FPS
        if getattr(self.current_scene, "FONDO_MENU", False):
            self.fondo_menu.update(dt)
        self._fundido = max(0.0, self._fundido - dt)

    def draw_game_elements(self):
        super().draw_game_elements()
        if self._fundido > 0 and self._foto is not None:
            self._foto.set_alpha(int(255 * self._fundido / C.FUNDIDO))
            self.screen.blit(self._foto, (0, 0))

    def aplicar_volumen(self):
        self.audio.set_volumenes(self.progreso.volumen_efectos, self.progreso.volumen_musica,
                                 self.progreso.volumen_voz)

    def salir(self):
        self.running = False

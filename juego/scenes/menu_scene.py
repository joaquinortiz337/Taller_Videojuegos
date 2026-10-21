# juego/scenes/menu_scene.py
from juego.scenes.base_menu import MenuBase
from juego import config as C


class MenuScene(MenuBase):
    """Menú principal: Jugar, Controles, Opciones, Salir."""
    TITULO = C.TITULO

    def __init__(self, game):
        super().__init__(game)
        cx = C.ANCHO // 2 - 140
        self.boton(cx, 190, 280, 60, "Jugar", lambda: self.game.change_scene("niveles"))
        self.boton(cx, 270, 280, 60, "Controles", lambda: self.game.change_scene("controles"))
        self.boton(cx, 350, 280, 60, "Opciones", lambda: self.game.change_scene("opciones"))
        self.boton(cx, 430, 280, 60, "Salir", self.game.salir)

    def on_enter(self):
        self.game.audio.musica("menu")

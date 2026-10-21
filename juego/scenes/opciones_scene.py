# juego/scenes/opciones_scene.py
from juego.scenes.base_menu import MenuBase
from juego import config as C


class OpcionesScene(MenuBase):
    TITULO = "Opciones"

    def __init__(self, game):
        super().__init__(game)
        cx = C.ANCHO // 2
        self.boton(cx - 220, 170, 60, 50, "-", lambda: self._cambiar("volumen_efectos", -0.1))
        self.boton(cx + 160, 170, 60, 50, "+", lambda: self._cambiar("volumen_efectos", +0.1))
        self.boton(cx - 220, 240, 60, 50, "-", lambda: self._cambiar("volumen_musica", -0.1))
        self.boton(cx + 160, 240, 60, 50, "+", lambda: self._cambiar("volumen_musica", +0.1))
        self.boton_borrar = self.boton(cx - 160, 330, 320, 55, "Borrar progreso", self._borrar)
        self.boton(cx - 140, 470, 280, 55, "Volver", lambda: self.game.change_scene("menu"))
        self.confirmando = False
        self.aviso = ""

    def on_enter(self):
        self.game.audio.musica("menu")

    def _cambiar(self, atributo, cambio):
        prog = self.game.progreso
        setattr(prog, atributo, getattr(prog, atributo) + cambio)
        self.game.aplicar_volumen()

    def _borrar(self):
        if not self.confirmando:
            # Primer clic: pide confirmación
            self.confirmando = True
            self.boton_borrar.text = "¿Seguro? Clic otra vez"
        else:
            self.game.progreso.borrar()
            self.confirmando = False
            self.boton_borrar.text = "Borrar progreso"
            self.aviso = "Progreso borrado"

    def draw(self, surface):
        super().draw(surface)
        prog = self.game.progreso
        for y, nombre, valor in ((195, "Efectos", prog.volumen_efectos), (265, "Música", prog.volumen_musica)):
            t = self.fuente.render(f"{nombre}: {int(round(valor * 100))}%", True, C.COLOR_TEXTO)
            surface.blit(t, t.get_rect(center=(C.ANCHO // 2, y)))
        if self.aviso:
            a = self.fuente_chica.render(self.aviso, True, (150, 0, 0))
            surface.blit(a, a.get_rect(center=(C.ANCHO // 2, 410)))

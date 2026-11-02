# juego/scenes/opciones_scene.py
from juego.scenes.base_menu import MenuBase
from juego import config as C
from juego import estilo as E


class OpcionesScene(MenuBase):
    TITULO = "Opciones"

    def __init__(self, game):
        super().__init__(game)
        cx = C.ANCHO // 2
        for y, atributo in ((165, "volumen_efectos"), (232, "volumen_musica"), (299, "volumen_voz")):
            self.boton(cx - 220, y, 60, 50, "-", lambda a=atributo: self._cambiar(a, -0.1))
            self.boton(cx + 160, y, 60, 50, "+", lambda a=atributo: self._cambiar(a, +0.1))
        self.boton_borrar = self.boton(cx - 160, 385, 320, 54, "Borrar progreso", self._borrar)
        self.boton(20, C.ALTO - 70, 160, 50, "Volver", lambda: self.game.change_scene("menu"))
        self.confirmando = False
        self.aviso = ""

    def on_enter(self):
        self.game.audio.musica("menu")

    def _cambiar(self, atributo, cambio):
        prog = self.game.progreso
        setattr(prog, atributo, getattr(prog, atributo) + cambio)
        self.game.aplicar_volumen()
        if atributo == "volumen_voz":
            self.game.audio.voz("good_job")   # para escuchar cómo queda

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
        self.dibujar_fondo(surface)
        E.panel(surface, (C.ANCHO // 2 - 260, 140, 520, 330))
        prog = self.game.progreso
        for y, nombre, valor in ((190, "Efectos", prog.volumen_efectos), (257, "Música", prog.volumen_musica),
                                 (324, "Narrador", prog.volumen_voz)):
            t = self.fuente.render(f"{nombre}: {int(round(valor * 100))}%", True, E.TEXTO)
            surface.blit(t, t.get_rect(center=(C.ANCHO // 2, y)))
        if self.aviso:
            a = self.fuente_chica.render(self.aviso, True, (255, 130, 110))
            surface.blit(a, a.get_rect(center=(C.ANCHO // 2, 455)))
        for b in self.botones:
            b.draw(surface)

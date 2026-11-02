# juego/scenes/creditos_scene.py
import pygame

from juego.scenes.base_menu import MenuBase
from juego import config as C
from juego import estilo as E

# (título de la sección, líneas)
CREDITOS = [
    ("Desarrollo", ["Joaquín Ortiz", "Facundo Cabrera"]),
    ("Voz del narrador", ["Joaquín Ortiz"]),
    ("Curso", ["Taller de Videojuegos 2D · 2026",
               "UTU"]),
    ("Gráficos, música y efectos", ["Generados por código"]),
    ("Hecho con", ["Python · Pygame · Pymunk", "Motor desarrollado en el curso"]),
    ("Fuentes", ["Lilita One (SIL Open Font License)", "FreeSans (GNU FreeFont)"]),
]


class CreditosScene(MenuBase):
    """Pantalla de créditos: se llega desde el menú principal o al ganar el último nivel.
    Cada sección: el título arriba y debajo los nombres, todo centrado."""
    TITULO = C.TITULO

    def __init__(self, game):
        super().__init__(game)
        self.fuente_seccion = E.fuente(24)
        self.fuente_nombre = pygame.font.Font(None, 27)
        self.boton(20, C.ALTO - 70, 250, 50, "Menú principal", lambda: self.game.change_scene("menu"))

    def on_enter(self):
        self.game.audio.musica("menu")

    def draw(self, surface):
        self.dibujar_fondo(surface)
        centro = C.ANCHO // 2
        alto = sum(26 + 21 * len(lineas) + 10 for _, lineas in CREDITOS)
        E.panel(surface, (centro - 215, 122, 430, alto + 12))
        y = 132
        for titulo, lineas in CREDITOS:
            t = self.fuente_seccion.render(titulo, True, E.DORADO_CLARO)
            surface.blit(t, t.get_rect(midtop=(centro, y)))
            y += 26
            for linea in lineas:
                n = self.fuente_nombre.render(linea, True, E.TEXTO)
                surface.blit(n, n.get_rect(midtop=(centro, y)))
                y += 21
            y += 10
        for b in self.botones:
            b.draw(surface)

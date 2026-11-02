# juego/camara.py
from engine.camera import Camera  # Hereda del motor


class CamaraManual(Camera):
    """
    La cámara del motor sigue a un objetivo; esta subclase agrega el
    movimiento manual (teclado y arrastre con el mouse), solo en horizontal.
    Convención del motor: camera_rect.x es NEGATIVO (desplazamiento a aplicar).
    """

    def __init__(self, ancho_pantalla, alto_pantalla, ancho_mundo, alto_mundo):
        super().__init__(ancho_pantalla, alto_pantalla, ancho_mundo, alto_mundo)

    @property
    def x(self):
        """Coordenada del mundo que se ve en el borde izquierdo de la pantalla."""
        return -self.camera_rect.x

    def ir_a(self, x):
        maximo = max(0, self.world_width - self.screen_width)
        self.camera_rect.x = -int(max(0, min(maximo, x)))

    def mover(self, dx):
        self.ir_a(self.x + dx)

    def centrar_en(self, x_mundo):
        self.ir_a(x_mundo - self.screen_width / 2)

    def a_mundo(self, pos_pantalla):
        return (pos_pantalla[0] + self.x, pos_pantalla[1])

    def visible(self, x_mundo, margen=0):
        return self.x - margen <= x_mundo <= self.x + self.screen_width + margen

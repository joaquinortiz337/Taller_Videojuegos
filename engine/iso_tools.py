"""
engine/iso_tools.py

Herramientas para dibujar en perspectiva isométrica.

La rejilla del mundo es cuadrada (grid_x, grid_y) pero se dibuja "en rombo".
Esta es la conversión clásica de 2:1 (por cada 2 px a lo ancho, 1 px a lo alto).
"""


def grid_to_iso(grid_x, grid_y, tile_width=64, tile_height=32):
    """Convierte una coordenada de rejilla a coordenadas de pantalla (isométrica)."""
    screen_x = (grid_x - grid_y) * (tile_width / 2)
    screen_y = (grid_x + grid_y) * (tile_height / 2)
    return screen_x, screen_y


def iso_to_grid(screen_x, screen_y, tile_width=64, tile_height=32):
    """Convierte coordenadas de pantalla a coordenadas de rejilla (inversa)."""
    grid_x = (screen_x / (tile_width / 2) + screen_y / (tile_height / 2)) / 2
    grid_y = (screen_y / (tile_height / 2) - screen_x / (tile_width / 2)) / 2
    return grid_x, grid_y


class IsoSprite:
    """
    Objeto colocado en una rejilla isométrica.

    Se posiciona por su celda (grid_x, grid_y); el motor calcula la posición
    de pantalla y el orden de dibujado (profundidad) para que lo que está
    "más atrás" se dibuje primero.
    """

    def __init__(self, grid_x, grid_y, image, tile_width=64, tile_height=32,
                 origin=(0, 0)):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.image = image
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.origin = origin
        self.screen_x = 0
        self.screen_y = 0
        self.rect = image.get_rect()
        self.update_screen_rect()

    def update_screen_rect(self):
        sx, sy = grid_to_iso(self.grid_x, self.grid_y,
                             self.tile_width, self.tile_height)
        self.screen_x = sx + self.origin[0]
        self.screen_y = sy + self.origin[1]
        # Se ancla por la base (midbottom) para que "apoye" en el suelo.
        self.rect = self.image.get_rect(midbottom=(self.screen_x, self.screen_y))

    @property
    def depth(self):
        """Clave de orden de dibujado: mayor profundidad = más adelante."""
        return self.grid_x + self.grid_y


def sort_by_depth(sprites):
    """Devuelve los sprites ordenados de atrás hacia adelante."""
    return sorted(sprites, key=lambda s: (s.depth, s.grid_y))

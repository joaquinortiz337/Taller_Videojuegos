# juego/hud.py
import pygame

from juego import config as C


def dibujar_energia(surface, fuente, energia):
    x, y, ancho, alto = 10, C.ALTO - 40, 220, 22
    pygame.draw.rect(surface, (30, 30, 30), (x, y, ancho, alto), border_radius=5)
    relleno = int((ancho - 4) * energia / C.ENERGIA_MAX)
    pygame.draw.rect(surface, (80, 170, 255), (x + 2, y + 2, relleno, alto - 4), border_radius=4)
    texto = fuente.render(f"Energía {int(energia)}", True, (255, 255, 255))
    surface.blit(texto, texto.get_rect(center=(x + ancho // 2, y + alto // 2)))


def rects_poderes(cantidad):
    """Rectángulos de las casillas de poderes (para dibujarlas y para detectar clics)."""
    ancho, alto, sep = 120, 52, 8
    total = cantidad * ancho + (cantidad - 1) * sep
    x0 = C.ANCHO - total - 10
    y = C.ALTO - alto - 6
    return [pygame.Rect(x0 + i * (ancho + sep), y, ancho, alto) for i in range(cantidad)]


def dibujar_poderes(surface, fuente, poderes, seleccionado):
    """Barra de poderes: tecla, nombre, nivel, costo y recarga."""
    for i, (poder, rect) in enumerate(zip(poderes, rects_poderes(len(poderes)))):
        x, y, ancho, alto = rect
        fondo = (50, 50, 80) if poder.disponible() else (70, 70, 70)
        pygame.draw.rect(surface, fondo, rect, border_radius=6)
        if poder is seleccionado:
            pygame.draw.rect(surface, (255, 220, 60), rect, 3, border_radius=6)

        # Sombra de recarga (se achica a medida que se recarga)
        if poder.recarga > 0 and poder.recarga_total > 0:
            prop = poder.recarga / poder.recarga_total
            sombra = pygame.Surface((ancho, int(alto * prop)), pygame.SRCALPHA)
            sombra.fill((0, 0, 0, 120))
            surface.blit(sombra, (x, y + alto - int(alto * prop)))

        color = (255, 255, 255) if poder.disponible() else (170, 170, 170)
        surface.blit(fuente.render(f"{i + 1}. {poder.nombre}", True, color), (x + 8, y + 6))
        detalle = f"Nv {poder.nivel} · {poder.costo}E"
        if poder.recarga > 0:
            detalle += f" · {int(poder.recarga) + 1}s"
        surface.blit(fuente.render(detalle, True, color), (x + 8, y + 28))


MINIMAPA = pygame.Rect(250, C.ALTO - 40, 225, 26)


def dibujar_minimapa(surface, ancho_mundo, camara_x, enemigos, alerta):
    """Barra con todo el nivel: base, enemigos (puntos) y lo que ve la cámara (rectángulo)."""
    r = MINIMAPA
    fondo = pygame.Surface(r.size, pygame.SRCALPHA)
    fondo.fill((20, 20, 30, 170))
    surface.blit(fondo, r.topleft)
    escala = r.w / ancho_mundo
    base_color = (230, 60, 40) if alerta else C.COLOR_BASE
    pygame.draw.rect(surface, base_color, (r.x, r.y, max(3, int(C.BASE_X * escala)), r.h))
    for e in enemigos:
        x = r.x + int(e.position.x * escala)
        if r.x <= x <= r.right:
            y = r.y + int(min(1.0, max(0.0, e.position.y / C.SUELO_Y)) * (r.h - 4)) + 2
            pygame.draw.circle(surface, (255, 90, 70), (x, y), 2 if e.radio < 20 else 3)
    vista = pygame.Rect(r.x + int(camara_x * escala), r.y, max(4, int(C.ANCHO * escala)), r.h)
    pygame.draw.rect(surface, (255, 255, 255), vista, 2)
    pygame.draw.rect(surface, (200, 200, 200), r, 1)


def _corazon(surface, centro, tam, color, borde=(60, 10, 10)):
    cx, cy = centro
    r = tam * 0.28
    izq, der = (cx - r, cy - r * 0.4), (cx + r, cy - r * 0.4)
    puntos = [(cx - 2 * r, cy - r * 0.2), (cx, cy + tam * 0.55), (cx + 2 * r, cy - r * 0.2)]
    pygame.draw.circle(surface, color, (int(izq[0]), int(izq[1])), int(r * 1.05))
    pygame.draw.circle(surface, color, (int(der[0]), int(der[1])), int(r * 1.05))
    pygame.draw.polygon(surface, color, puntos)
    pygame.draw.circle(surface, borde, (int(izq[0]), int(izq[1])), int(r * 1.05), 2)
    pygame.draw.circle(surface, borde, (int(der[0]), int(der[1])), int(r * 1.05), 2)
    pygame.draw.lines(surface, borde, False, puntos, 2)


def dibujar_corazones(surface, vidas, maximo, perdiendo):
    """Vida de la base: corazones rojos (los que quedan) y grises (los perdidos).
    'perdiendo' = {índice: segundos}: el corazón recién perdido titila y se encoge."""
    for i in range(maximo):
        centro = (24 + i * 34, 22)
        if i < vidas:
            _corazon(surface, centro, 28, (225, 40, 50))
        elif i in perdiendo:
            t = perdiendo[i]
            if int(t * 14) % 2 == 0:
                _corazon(surface, centro, int(28 * (0.5 + t / 1.2)), (255, 120, 120))
            else:
                _corazon(surface, centro, 28, (110, 110, 110), (40, 40, 40))
        else:
            _corazon(surface, centro, 28, (110, 110, 110), (40, 40, 40))


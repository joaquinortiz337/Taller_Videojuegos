# juego/cursores.py
# Imágenes del cursor dibujadas por código (después se pueden reemplazar por sprites).
import math
import pygame

PIEL = (245, 215, 180)
BORDE = (60, 40, 30)


def mano_abierta(tam=34):
    img = pygame.Surface((tam, tam), pygame.SRCALPHA)
    palma = pygame.Rect(tam * 0.25, tam * 0.45, tam * 0.5, tam * 0.42)
    for i in range(4):                                     # dedos
        x = palma.x + 1 + i * palma.w / 4
        dedo = pygame.Rect(x, tam * 0.12 + abs(1.5 - i) * 3, palma.w / 4 - 1, tam * 0.4)
        pygame.draw.rect(img, PIEL, dedo, border_radius=4)
        pygame.draw.rect(img, BORDE, dedo, 1, border_radius=4)
    pulgar = pygame.Rect(tam * 0.08, tam * 0.5, tam * 0.22, tam * 0.13)
    pygame.draw.rect(img, PIEL, pulgar, border_radius=4)
    pygame.draw.rect(img, BORDE, pulgar, 1, border_radius=4)
    pygame.draw.rect(img, PIEL, palma, border_radius=6)
    pygame.draw.rect(img, BORDE, palma, 1, border_radius=6)
    return img


def mano_cerrada(tam=34):
    img = pygame.Surface((tam, tam), pygame.SRCALPHA)
    puño = pygame.Rect(tam * 0.2, tam * 0.3, tam * 0.6, tam * 0.5)
    pygame.draw.rect(img, PIEL, puño, border_radius=8)
    pygame.draw.rect(img, BORDE, puño, 1, border_radius=8)
    for i in range(1, 4):                                  # nudillos
        x = puño.x + i * puño.w / 4
        pygame.draw.line(img, BORDE, (x, puño.y + 2), (x, puño.y + puño.h * 0.45), 1)
    pulgar = pygame.Rect(tam * 0.22, tam * 0.55, tam * 0.4, tam * 0.14)
    pygame.draw.rect(img, PIEL, pulgar, border_radius=4)
    pygame.draw.rect(img, BORDE, pulgar, 1, border_radius=4)
    return img


def icono_poder(clave, tam=30):
    """Ícono que muestra el cursor cuando hay un poder seleccionado."""
    img = pygame.Surface((tam, tam), pygame.SRCALPHA)
    c = tam // 2
    if clave == "bomba":
        pygame.draw.circle(img, (35, 35, 35), (c, c + 3), tam // 3)
        pygame.draw.line(img, (150, 110, 60), (c, c + 3 - tam // 3), (c + 5, 2), 2)
        pygame.draw.circle(img, (255, 170, 40), (c + 5, 3), 3)
    elif clave == "agujero":
        pygame.draw.circle(img, (120, 60, 200), (c, c), tam // 2 - 1, 3)
        pygame.draw.circle(img, (10, 0, 20), (c, c), tam // 4)
    elif clave == "muro":
        for fila in range(3):
            for col in range(2):
                desplaz = 5 if fila % 2 else 0
                r = pygame.Rect(2 + col * 13 + desplaz, 4 + fila * 8, 12, 7)
                pygame.draw.rect(img, (150, 100, 50), r)
                pygame.draw.rect(img, (40, 30, 20), r, 1)
    elif clave == "rayo":
        puntos = [(c + 4, 1), (c - 6, c + 2), (c, c + 2), (c - 4, tam - 1), (c + 7, c - 3), (c + 1, c - 3)]
        pygame.draw.polygon(img, (255, 235, 70), puntos)
        pygame.draw.polygon(img, (120, 90, 0), puntos, 1)
    return img

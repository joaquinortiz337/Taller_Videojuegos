# juego/ui_extra.py
import math
import pygame

from engine.ui import Button  # Hereda del motor


class SoundButton(Button):
    """
    Botón del motor + sonido al hacer clic (requisito del enunciado).
    Estilo del juego: degradé, borde dorado, sombra, crece al pasar el mouse y se hunde al apretarlo.
    Si se le pasan colores propios (ej: el panel de prueba) se dibuja con el estilo simple del motor.
    """

    def __init__(self, x, y, width, height, text, callback, sound=None, **estilo):
        super().__init__(x, y, width, height, text, callback, **estilo)
        self.sound = sound
        self.seleccionado = False   # para resaltar (ej: dificultad elegida)
        self.simple = bool(estilo)
        self.escala = 1.0
        self.color_arriba = None    # colores propios del degradé (ej: botones de dificultad)
        self.color_abajo = None
        self.color_texto = None
        self.activo = True          # False: se ve gris y no crece (ej: "Mejorar" sin estrellas)
        if not self.simple:
            from juego import estilo as E
            self.font = E.fuente(max(16, int(height * 0.5)))
        self._imagenes = {}

    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos) and self.sound):
            self.sound.play()
        super().handle_event(event)

    def _fondo(self, tam, encima):
        from juego import estilo as E
        clave = (tam, encima, self.color_arriba, self.color_abajo)
        if clave not in self._imagenes:
            arriba = self.color_arriba or E.BOTON_ARRIBA
            abajo = self.color_abajo or E.BOTON_ABAJO
            if encima:   # más claro
                arriba = tuple(min(255, c + 32) for c in arriba)
                abajo = tuple(min(255, c + 14) for c in abajo)
            self._imagenes[clave] = E.degrade_redondeado(tam, arriba, abajo, 14)
        return self._imagenes[clave]

    def draw(self, surface):
        if self.simple:
            super().draw(surface)
            if self.seleccionado:
                pygame.draw.rect(surface, (255, 220, 60), self.rect, 3, border_radius=8)
            return
        from juego import estilo as E
        r = self.dibujar_base(surface)
        color = (165, 165, 175) if not self.activo else (self.color_texto or E.TEXTO)
        texto = self.font.render(self.text, True, color)
        surface.blit(texto, texto.get_rect(center=(r.centerx, r.centery + 1)))

    def dibujar_base(self, surface):
        """Dibuja sombra, degradé y borde; devuelve el rectángulo donde quedó (para el texto)."""
        from juego import estilo as E
        encima = self.rect.collidepoint(pygame.mouse.get_pos()) and self.activo
        apretado = encima and pygame.mouse.get_pressed()[0]
        objetivo = 1.05 if encima else 1.0
        self.escala += (objetivo - self.escala) * 0.25
        w = int(self.rect.w * self.escala)
        h = int(self.rect.h * self.escala)
        r = pygame.Rect(0, 0, w, h)
        r.center = self.rect.center
        if apretado:
            r.y += 3
        sombra = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (5, 3, 15, 150), (0, 0, w, h), border_radius=14)
        surface.blit(sombra, (r.x, r.y + (2 if apretado else 5)))
        if self.activo:
            surface.blit(self._fondo((w, h), encima), r)
            borde = E.DORADO_CLARO if (encima or self.seleccionado) else E.DORADO
        else:
            surface.blit(self._fondo_gris((w, h)), r)
            borde = (120, 120, 130)
        pygame.draw.rect(surface, borde, r, 4 if self.seleccionado else 2, border_radius=14)
        return r

    def _fondo_gris(self, tam):
        from juego import estilo as E
        clave = (tam, "gris")
        if clave not in self._imagenes:
            self._imagenes[clave] = E.degrade_redondeado(tam, (95, 95, 108), (62, 62, 74), 14)
        return self._imagenes[clave]


def dibujar_estrella(surface, centro, radio, llena=True):
    """Estrella de 5 puntas: amarilla si está conseguida, gris si no."""
    cx, cy = centro
    puntos = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = radio if i % 2 == 0 else radio * 0.45
        puntos.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    color = (255, 210, 50) if llena else (110, 110, 110)
    pygame.draw.polygon(surface, color, puntos)
    pygame.draw.polygon(surface, (60, 50, 20), puntos, 2)


def dibujar_texto_multilinea(surface, fuente, texto, color, x, y, ancho_max, interlineado=4):
    """Escribe un texto partiéndolo en varias líneas para que no pase de ancho_max."""
    palabras = texto.split()
    linea = ""
    for palabra in palabras:
        prueba = (linea + " " + palabra).strip()
        if fuente.size(prueba)[0] > ancho_max and linea:
            surface.blit(fuente.render(linea, True, color), (x, y))
            y += fuente.get_height() + interlineado
            linea = palabra
        else:
            linea = prueba
    if linea:
        surface.blit(fuente.render(linea, True, color), (x, y))
        y += fuente.get_height() + interlineado
    return y

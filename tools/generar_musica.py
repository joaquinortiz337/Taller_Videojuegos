"""
tools/generar_musica.py

Genera por código (síntesis) la música del juego en assets/music/:
  menu.wav               -> tema tranquilo de los menús
  partida_base.wav       -> capa que suena siempre en la partida (bajo, acordes, melodía)
  partida_tension.wav    -> capa que sube con el peligro (arpegio rápido)
  partida_percusion.wav  -> capa que entra con mucho peligro o con combos (batería)
Las tres capas de la partida duran exactamente lo mismo y suenan a la vez, sincronizadas:
el juego solo cambia el volumen de cada una.
No usa archivos de terceros. Requiere numpy (solo para generar; el juego no lo necesita).

Uso (desde la carpeta del proyecto):
    python tools/generar_musica.py
"""
import os
import wave

import numpy as np

SR = 22050
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "assets", "music")
rng = np.random.default_rng(7)


# ---------------- Utilidades ----------------
def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def onda(forma, f, n):
    tt = np.arange(n) / SR
    fase = 2 * np.pi * f * tt
    if forma == "sin":
        return np.sin(fase)
    if forma == "triangulo":
        return 2 / np.pi * np.arcsin(np.sin(fase))
    if forma == "cuadrada":       # cuadrada suave (menos chillona)
        return np.tanh(3 * np.sin(fase))
    if forma == "sierra":         # pocos armónicos: más cálida
        return sum(np.sin(fase * k) / k for k in range(1, 7)) * 0.6
    raise ValueError(forma)


def adsr(n, ataque=0.01, caida=0.1, sostenido=0.7, liberacion=0.1):
    """Envolvente; la liberación se agrega después del final de la nota."""
    total = n + int(SR * liberacion)
    e = np.zeros(total)
    a = max(1, int(SR * ataque))
    d = max(1, int(SR * caida))
    e[:a] = np.linspace(0, 1, a)
    fin_d = min(n, a + d)
    e[a:fin_d] = np.linspace(1, sostenido, fin_d - a)
    e[fin_d:n] = sostenido
    nivel = e[n - 1] if n > 0 else sostenido
    e[n:] = nivel * np.exp(-np.arange(total - n) / (SR * liberacion / 4))
    return e


def nota(forma, midi, dur, vol=1.0, **env):
    n = int(SR * dur)
    e = adsr(n, **env)
    return onda(forma, hz(midi), len(e)) * e * vol


def pasabajos(x, alfa):
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alfa * (v - acc)
        y[i] = acc
    return y


def pasaaltos(x, alfa):
    return x - pasabajos(x, alfa)


def poner(buffer, inicio_seg, senal):
    """Suma la señal al buffer; lo que pasa del final vuelve al principio (bucle sin cortes)."""
    i = int(inicio_seg * SR)
    idx = (np.arange(len(senal)) + i) % len(buffer)
    np.add.at(buffer, idx, senal)


def guardar(nombre, x):
    os.makedirs(DESTINO, exist_ok=True)
    datos = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(os.path.join(DESTINO, nombre + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(datos.tobytes())
    print("  ", nombre, f"{len(x) / SR:.1f} s")


# ---------------- Batería ----------------
def bombo(vol=1.0):
    d = 0.3
    n = int(SR * d)
    tt = np.arange(n) / SR
    f = 45 + 80 * np.exp(-tt * 30)
    fase = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(fase) * np.exp(-tt * 9) * vol


def caja(vol=1.0):
    d = 0.22
    n = int(SR * d)
    tt = np.arange(n) / SR
    r = pasaaltos(rng.uniform(-1, 1, n), 0.25) * np.exp(-tt * 18)
    tono = np.sin(2 * np.pi * 185 * tt) * np.exp(-tt * 25)
    return (0.8 * r + 0.5 * tono) * vol


def platillo_cerrado(vol=1.0):
    n = int(SR * 0.05)
    tt = np.arange(n) / SR
    return pasaaltos(rng.uniform(-1, 1, n), 0.6) * np.exp(-tt * 70) * vol


def platillo_crash(vol=1.0):
    n = int(SR * 1.4)
    tt = np.arange(n) / SR
    return pasaaltos(rng.uniform(-1, 1, n), 0.5) * np.exp(-tt * 3) * vol


def tambor(midi, vol=1.0):
    n = int(SR * 0.25)
    tt = np.arange(n) / SR
    f = hz(midi) * (1 + 0.5 * np.exp(-tt * 20))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 12) * vol


# ---------------- Acordes (La menor) ----------------
#  raíz MIDI (octava del bajo) y notas del acorde (para pad y arpegios)
ACORDES = {
    "Am": (45, [57, 60, 64]), "F": (41, [53, 57, 60]), "C": (48, [55, 60, 64]),
    "G": (43, [55, 59, 62]), "Dm": (38, [50, 53, 57]), "E": (40, [52, 56, 59]),
}


def tema_partida():
    bpm = 128
    negra = 60 / bpm
    compas = 4 * negra
    progresion = ["Am", "F", "C", "G", "Am", "F", "Dm", "E",
                  "F", "G", "Am", "Am", "F", "G", "E", "E"]
    largo = int(SR * compas * len(progresion))
    base = np.zeros(largo)
    tension = np.zeros(largo)
    perc = np.zeros(largo)

    # Melodía de la parte A (8 compases) y B, en corcheas/negras: (tiempo en negras, midi, duración)
    melodia_a = [(0, 69, 1), (1, 72, 0.5), (1.5, 71, 0.5), (2, 69, 1), (3, 64, 1),
                 (4, 65, 1.5), (5.5, 64, 0.5), (6, 65, 1), (7, 69, 1),
                 (8, 67, 1), (9, 64, 1), (10, 67, 1), (11, 72, 1),
                 (12, 71, 2), (14, 67, 2),
                 (16, 69, 1), (17, 72, 0.5), (17.5, 71, 0.5), (18, 69, 1), (19, 76, 1),
                 (20, 77, 1.5), (21.5, 76, 0.5), (22, 72, 1), (23, 69, 1),
                 (24, 74, 1), (25, 72, 1), (26, 69, 1), (27, 65, 1),
                 (28, 68, 2), (30, 71, 2)]
    melodia_b = [(0, 72, 1), (1, 69, 1), (2, 65, 1), (3, 69, 1),
                 (4, 71, 1), (5, 67, 1), (6, 62, 1), (7, 67, 1),
                 (8, 72, 1.5), (9.5, 71, 0.5), (10, 69, 2),
                 (12, 76, 1), (13, 74, 0.5), (13.5, 72, 0.5), (14, 71, 1), (15, 69, 1),
                 (16, 72, 1), (17, 69, 1), (18, 65, 1), (19, 69, 1),
                 (20, 74, 1), (21, 71, 1), (22, 67, 1), (23, 74, 1),
                 (24, 71, 2), (26, 68, 2),
                 (28, 71, 1), (29, 74, 1), (30, 76, 2)]

    for i, nombre in enumerate(progresion):
        t0 = i * compas
        raiz, notas = ACORDES[nombre]
        # --- Base: bajo en corcheas (raíz y octava) + pad ---
        for k in range(8):
            midi = raiz + (12 if k % 2 else 0)
            poner(base, t0 + k * negra / 2,
                  nota("triangulo", midi, negra / 2 * 0.9, 0.55, ataque=0.005, caida=0.08,
                       sostenido=0.6, liberacion=0.04))
        for midi in notas:
            poner(base, t0, pasabajos(nota("sierra", midi, compas, 0.11, ataque=0.15, caida=0.3,
                                           sostenido=0.8, liberacion=0.3), 0.15))
        # Shaker suave a contratiempo (mantiene el ritmo aunque no haya batería)
        for k in range(4):
            poner(base, t0 + (k + 0.5) * negra, platillo_cerrado(0.12))

        # --- Tensión: arpegio en semicorcheas una octava arriba + pulso grave ---
        patron = [0, 1, 2, 1, 0, 2, 1, 2]
        for k in range(16):
            midi = notas[patron[k % 8]] + 12
            poner(tension, t0 + k * negra / 4,
                  nota("cuadrada", midi, negra / 4 * 0.8, 0.28, ataque=0.003, caida=0.05,
                       sostenido=0.4, liberacion=0.03))
            poner(tension, t0 + k * negra / 4,
                  nota("sierra", raiz + 12, negra / 4 * 0.6, 0.16, ataque=0.003, caida=0.04,
                       sostenido=0.5, liberacion=0.02))

        # --- Percusión ---
        for k in range(4):
            poner(perc, t0 + k * negra, bombo(0.75 if k in (0, 2) else 0.45))
            if k in (1, 3):
                poner(perc, t0 + k * negra, caja(0.6))
        poner(perc, t0 + 3.5 * negra, bombo(0.6))
        for k in range(16):
            poner(perc, t0 + k * negra / 4, platillo_cerrado(0.22 if k % 2 == 0 else 0.12))
        if i % 8 == 0:
            poner(perc, t0, platillo_crash(0.3))
        if i % 8 == 7:   # redoble de tambores al final de cada parte
            for k, midi in enumerate((50, 50, 47, 47, 43, 43, 40, 40)):
                poner(perc, t0 + 2 * negra + k * negra / 4, tambor(midi, 0.5))

    # Melodías (en la base, para que suene completo aunque no haya tensión)
    for parte, melodia in ((0, melodia_a), (8, melodia_b)):
        for tiempo, midi, dur in melodia:
            inicio = parte * compas + tiempo * negra
            voz = nota("triangulo", midi, dur * negra * 0.9, 0.22, ataque=0.01, caida=0.1,
                       sostenido=0.7, liberacion=0.08)
            voz += nota("cuadrada", midi + 12, dur * negra * 0.9, 0.03, ataque=0.01, caida=0.1,
                        sostenido=0.6, liberacion=0.08)
            poner(base, inicio, voz)

    # Mismo factor para las tres capas: todas juntas no saturan
    pico = np.max(np.abs(base + tension + perc))
    factor = 0.9 / pico
    return base * factor, tension * factor, perc * factor


def tema_menu():
    bpm = 92
    negra = 60 / bpm
    compas = 4 * negra
    acordes = {"C": (48, [60, 64, 67]), "Am": (45, [57, 60, 64]), "F": (41, [57, 60, 65]),
               "G": (43, [59, 62, 67]), "Em": (40, [55, 59, 64])}
    progresion = ["C", "Am", "F", "G", "C", "Em", "F", "G"]
    largo = int(SR * compas * len(progresion))
    x = np.zeros(largo)
    campana = [(0, 76, 2), (2, 79, 2), (4, 72, 3), (8, 77, 2), (10, 76, 1), (11, 74, 1),
               (12, 74, 4), (16, 76, 2), (18, 79, 2), (20, 83, 3), (24, 81, 2), (26, 79, 2), (28, 74, 4)]
    for i, nombre in enumerate(progresion):
        t0 = i * compas
        raiz, notas = acordes[nombre]
        poner(x, t0, nota("triangulo", raiz, compas * 0.95, 0.35, ataque=0.05, caida=0.3,
                          sostenido=0.6, liberacion=0.3))
        for midi in notas:
            poner(x, t0, pasabajos(nota("sierra", midi, compas, 0.07, ataque=0.4, caida=0.3,
                                        sostenido=0.8, liberacion=0.5), 0.1))
        patron = [0, 1, 2, 1, 0, 2, 1, 2]
        for k in range(8):   # arpegio suave en corcheas
            poner(x, t0 + k * negra / 2, nota("sin", notas[patron[k]] + 12, negra * 0.45, 0.13,
                                              ataque=0.005, caida=0.2, sostenido=0.2, liberacion=0.25))
    for tiempo, midi, dur in campana:
        poner(x, tiempo * negra, nota("sin", midi, dur * negra, 0.16, ataque=0.005, caida=0.6,
                                      sostenido=0.3, liberacion=0.6))
        poner(x, tiempo * negra, nota("sin", midi + 12, dur * negra, 0.04, ataque=0.005, caida=0.3,
                                      sostenido=0.1, liberacion=0.4))
    return x * (0.8 / np.max(np.abs(x)))


if __name__ == "__main__":
    print("Generando música en", DESTINO)
    base, tension, perc = tema_partida()
    guardar("partida_base", base)
    guardar("partida_tension", tension)
    guardar("partida_percusion", perc)
    guardar("menu", tema_menu())
    print("Listo.")

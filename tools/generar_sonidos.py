"""
tools/generar_sonidos.py

Genera por código (síntesis) todos los efectos de sonido del juego en assets/sounds/.
No usa archivos de terceros, así que no hay problemas de licencias.
Requiere numpy:  pip install numpy   (solo para generar; el juego no lo necesita)

Uso (desde la carpeta del proyecto):
    python tools/generar_sonidos.py
"""
import os
import wave

import numpy as np

SR = 44100
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "assets", "sounds")
rng = np.random.default_rng(42)


def t(dur):
    return np.linspace(0, dur, int(SR * dur), endpoint=False)


def env(n, ataque=0.005, caida=8.0):
    """Envolvente: sube rápido y cae exponencialmente."""
    x = np.arange(n) / SR
    a = np.clip(x / max(ataque, 1e-4), 0, 1)
    return a * np.exp(-caida * x)


def ruido(dur):
    return rng.uniform(-1, 1, int(SR * dur))


def pasabajos(x, alfa):
    """Filtro pasabajos simple (alfa chico = más grave)."""
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alfa * (v - acc)
        y[i] = acc
    return y


def barrido(f0, f1, dur, forma="sin"):
    tt = t(dur)
    f = np.linspace(f0, f1, len(tt))
    fase = 2 * np.pi * np.cumsum(f) / SR
    if forma == "cuadrada":
        return np.sign(np.sin(fase))
    return np.sin(fase)


def guardar(nombre, x, volumen=0.8):
    x = x / (np.max(np.abs(x)) + 1e-9) * volumen
    datos = (x * 32767).astype(np.int16)
    with wave.open(os.path.join(DESTINO, nombre + ".wav"), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(datos.tobytes())
    print("  ", nombre)


def generar():
    os.makedirs(DESTINO, exist_ok=True)
    print("Generando sonidos en", DESTINO)

    # Golpes secos (3 variantes)
    for i, (f0, alfa) in enumerate([(110, 0.08), (95, 0.06), (130, 0.1)], 1):
        d = 0.22
        cuerpo = barrido(f0, f0 * 0.5, d) * env(int(SR * d), caida=18)
        chasquido = pasabajos(ruido(d), alfa) * env(int(SR * d), caida=40)
        guardar(f"golpe_{i}", cuerpo + 1.5 * chasquido, 0.85)

    # Crujidos de bloques según material
    d = 0.35
    madera = pasabajos(ruido(d), 0.25) * env(int(SR * d), caida=14)
    madera += 0.5 * barrido(320, 180, d) * env(int(SR * d), caida=20)
    guardar("crujido_madera", madera)
    piedra = pasabajos(ruido(d), 0.12) * env(int(SR * d), caida=10)
    piedra += 0.6 * barrido(90, 60, d) * env(int(SR * d), caida=12)
    guardar("crujido_piedra", piedra)
    d = 0.6
    tt = t(d)
    metal = sum(np.sin(2 * np.pi * f * tt) * a for f, a in [(620, 1), (1310, 0.6), (2210, 0.4), (3400, 0.25)])
    metal = metal * env(len(tt), caida=6) + 0.3 * ruido(d) * env(len(tt), caida=50)
    guardar("crujido_metal", metal, 0.6)

    # Mano: agarrar (pop) y lanzar (whoosh)
    d = 0.08
    guardar("agarrar", barrido(500, 900, d) * env(int(SR * d), caida=40), 0.5)
    d = 0.3
    whoosh = pasabajos(ruido(d), 0.15)
    forma = np.sin(np.linspace(0, np.pi, len(whoosh))) ** 2
    guardar("lanzar", whoosh * forma, 0.5)

    # Muerte de enemigo (plop)
    d = 0.18
    guardar("muerte", barrido(600, 150, d) * env(int(SR * d), caida=18), 0.6)

    # Armadura rota (metal + crujido)
    d = 0.5
    tt = t(d)
    arm = sum(np.sin(2 * np.pi * f * tt) * a for f, a in [(440, 1), (970, 0.7), (1650, 0.4)])
    arm = arm * env(len(tt), caida=9) + 0.8 * pasabajos(ruido(d), 0.3) * env(len(tt), caida=20)
    guardar("armadura", arm, 0.7)

    # Mecha (siseo, pensado para repetirse en bucle)
    d = 0.5
    sis = ruido(d) - pasabajos(ruido(d), 0.2)        # ruido agudo
    sis *= 0.6 + 0.4 * np.sin(2 * np.pi * 18 * t(d))  # chisporroteo
    guardar("mecha", sis, 0.25)

    # Explosión
    d = 1.0
    boom = pasabajos(ruido(d), 0.04) * env(int(SR * d), ataque=0.003, caida=4)
    boom += 0.8 * barrido(70, 30, d) * env(int(SR * d), caida=5)
    boom += 0.4 * pasabajos(ruido(d), 0.4) * env(int(SR * d), caida=25)
    guardar("explosion", boom, 0.95)

    # Agujero negro (zumbido grave en bucle)
    d = 1.0
    tt = t(d)
    hum = np.sin(2 * np.pi * 55 * tt) + 0.5 * np.sin(2 * np.pi * 110 * tt) + 0.3 * np.sin(2 * np.pi * 57 * tt)
    hum *= 0.8 + 0.2 * np.sin(2 * np.pi * 3 * tt)
    guardar("agujero", hum, 0.35)

    # Muro (golpe de piedra al aparecer)
    d = 0.4
    muro = barrido(80, 40, d) * env(int(SR * d), caida=10) + pasabajos(ruido(d), 0.1) * env(int(SR * d), caida=16)
    guardar("muro", muro, 0.8)

    # Rayo (chasquido eléctrico)
    d = 0.6
    chas = ruido(d) * env(int(SR * d), ataque=0.001, caida=7)
    chas *= (rng.uniform(0, 1, len(chas)) > 0.6)          # crepitar
    chas += 0.5 * pasabajos(ruido(d), 0.05) * env(int(SR * d), caida=5)
    guardar("rayo", chas, 0.8)

    # Combo: ping que sube de tono (combo 2 a 6)
    for n in range(2, 7):
        d = 0.25
        f = 660 * (2 ** ((n - 2) * 2 / 12))
        tt = t(d)
        ping = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)) * env(len(tt), caida=12)
        guardar(f"combo_{n}", ping, 0.5)

    # Base: golpe grave
    d = 0.5
    guardar("base_golpe", (barrido(120, 45, d) + 0.5 * pasabajos(ruido(d), 0.05)) * env(int(SR * d), caida=7), 0.9)

    # Alarma (dos tonos)
    partes = []
    for f in (880, 660, 880, 660):
        d = 0.12
        partes.append(barrido(f, f, d, "cuadrada") * env(int(SR * d), ataque=0.005, caida=3))
    guardar("alarma", np.concatenate(partes), 0.35)

    # Error (zumbido corto)
    d = 0.18
    guardar("error", barrido(160, 140, d, "cuadrada") * env(int(SR * d), caida=6), 0.35)

    # Jingles de victoria y derrota
    def melodia(notas, dur=0.16):
        sal = []
        for f in notas:
            tt = t(dur)
            sal.append((np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)) * env(len(tt), caida=5))
        return np.concatenate(sal)
    guardar("victoria", melodia([523, 659, 784, 1047, 784, 1047], 0.15), 0.6)
    guardar("derrota", melodia([392, 349, 311, 262], 0.28), 0.6)

    # Corte de la cuerda de la mano (chasquido agudo)
    d = 0.12
    corte = (ruido(d) - pasabajos(ruido(d), 0.3)) * env(int(SR * d), ataque=0.001, caida=40)
    corte += 0.6 * barrido(1800, 600, d) * env(int(SR * d), caida=30)
    guardar("corte", corte, 0.55)

    # Clic de botones
    d = 0.06
    guardar("click", np.sin(2 * np.pi * 1200 * t(d)) * env(int(SR * d), caida=80), 0.5)

    # Chamán curando (campanitas que suben)
    partes = []
    for f in (784, 988, 1175, 1568):
        d = 0.09
        tt = t(d)
        partes.append((np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * 3 * f * tt)) * env(len(tt), caida=14))
    d = 0.5
    cola = np.sin(2 * np.pi * 1568 * t(d)) * env(int(SR * d), caida=9)
    guardar("curar", np.concatenate(partes + [0.6 * cola]), 0.45)

    # Animador (grito corto que sube, tipo "¡vamos!")
    d = 0.35
    grito = barrido(300, 700, d, "cuadrada") * env(int(SR * d), ataque=0.02, caida=7)
    grito = pasabajos(grito, 0.25) + 0.3 * barrido(600, 1400, d) * env(int(SR * d), caida=10)
    guardar("animar", grito, 0.45)

    # Pisotón del jefe (golpe muy grave + tierra)
    d = 0.8
    pis = 1.2 * barrido(60, 25, d) * env(int(SR * d), ataque=0.002, caida=6)
    pis += pasabajos(ruido(d), 0.03) * env(int(SR * d), ataque=0.002, caida=5)
    pis += 0.3 * pasabajos(ruido(d), 0.3) * env(int(SR * d), caida=20)
    guardar("pisoton", pis, 0.95)

    # Mejora comprada (destello que sube)
    partes = []
    for f in (523, 659, 784, 1047):
        d = 0.07
        tt = t(d)
        partes.append(np.sin(2 * np.pi * f * tt) * env(len(tt), caida=10))
    d = 0.45
    tt = t(d)
    brillo = (np.sin(2 * np.pi * 1047 * tt) + 0.5 * np.sin(2 * np.pi * 1568 * tt)) * env(len(tt), caida=6)
    brillo *= 0.8 + 0.2 * np.sin(2 * np.pi * 12 * tt)
    guardar("mejora", np.concatenate(partes + [brillo]), 0.5)

    # Cristal de energía (campanada de vidrio con brillo)
    d = 0.9
    tt = t(d)
    vidrio = sum(peso * np.sin(2 * np.pi * f * tt) * env(len(tt), ataque=0.001, caida=c)
                 for f, peso, c in ((1319, 1.0, 5), (2637, 0.5, 8), (3951, 0.3, 12), (1760, 0.4, 6)))
    vidrio += 0.15 * (ruido(d) - pasabajos(ruido(d), 0.3)) * env(len(tt), ataque=0.001, caida=40)
    guardar("cristal", vidrio, 0.5)

    # Latido (último corazón): "pum-pum" grave
    def pum(f, d=0.16):
        tt = t(d)
        return np.sin(2 * np.pi * f * tt * (1 + 0.3 * np.exp(-tt * 30))) * env(len(tt), ataque=0.004, caida=22)
    latido = np.concatenate([pum(62), np.zeros(int(SR * 0.09)), 0.7 * pum(55), np.zeros(int(SR * 0.1))])
    guardar("latido", pasabajos(latido, 0.2), 0.9)


if __name__ == "__main__":
    generar()

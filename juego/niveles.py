# juego/niveles.py
# Los niveles se definen como DATOS. Agregar un nivel = agregar una entrada acá.
#
# "aparicion" define el ritmo de los enemigos (ver juego/director.py):
#   total:              cuántos enemigos tiene el nivel (en Normal)
#   min_vivos/max_vivos: cuántos puede haber vivos a la vez
#   intervalo_base:     segundos entre apariciones con 0 enemigos vivos...
#   intervalo_por_vivo: ...más esto por cada enemigo vivo
#   reemplazo:          probabilidad de que entre otro al instante al matar uno
#   etapas:             qué tipos aparecen según cuánto del nivel pasó (0 a 1)
#   fijos:              grupos que aparecen sí o sí en un momento del nivel
#                       (en=1.0: grupo final, lo último que aparece, en el orden escrito)
# "desde" indica la dificultad mínima en la que existe esa parte.


def tipo(clave, peso=1, desde="normal"):
    return dict(clave=clave, peso=peso, desde=desde)


def etapa(hasta, *tipos):
    return dict(hasta=hasta, tipos=list(tipos))


def fijo(en, enemigos, desde="normal"):
    """en: parte del nivel (0 a 1) en la que aparece. enemigos: [(tipo, cantidad), ...]"""
    return dict(en=en, enemigos=enemigos, desde=desde)


NIVELES = [
    dict(
        id="nivel1",
        nombre="La Pradera",
        descripcion="Los primeros invasores llegan a la pradera. Aprendé a agarrarlos y revolearlos.",
        posicion=(200, 300),      # dónde aparece el botón en la selección de niveles
        disponible=True,
        ancho=2500,               # largo del nivel en píxeles
        fondo="pradera",          # paleta del fondo (ver juego/fondo.py)
        barriles=[700, 1500],     # posición x de cada barril al empezar
        suelos=[(1150, 1400, "barro")],   # tramos de suelo especial: (desde x, hasta x, tipo) (ver C.SUELOS)
        # Lomas suaves: (x, desnivel). Negativo = más alto. Cerca de la base y de la entrada, plano.
        terreno=[(0, 0), (300, 0), (700, -55), (1100, -15), (1500, -60), (1900, -20),
                 (2250, 0), (2500, 0)],
        aparicion=dict(
            total=40, min_vivos=2, max_vivos=8,
            intervalo_base=1.6, intervalo_por_vivo=0.3, reemplazo=0.3,
            etapas=[
                etapa(0.25, tipo("comun_chico")),
                etapa(0.6, tipo("comun_chico", 3), tipo("comun_mediano", 2)),
                etapa(1.0, tipo("comun_chico", 2), tipo("comun_mediano", 3), tipo("comun_grande", 1),
                      tipo("comun_grande", 1, desde="dificil")),
            ],
            fijos=[
                fijo(0.35, [("comun_grande", 1), ("comun_chico", 3)]),   # el primer grande, escoltado
                fijo(0.85, [("comun_chico", 6)]),                        # avalancha de chicos
                fijo(0.95, [("comun_grande", 2)], desde="experto"),
            ],
        ),
    ),
    dict(
        id="nivel2",
        nombre="El Bosque",
        descripcion="Entre los árboles se esconden enemigos más rápidos... y algunos que no conviene tener cerca.",
        posicion=(420, 220),
        disponible=True,
        ancho=2500,
        fondo="bosque",
        barriles=[750, 1500, 1950],
        suelos=[(1000, 1300, "barro"), (1680, 1900, "barro")],
        terreno=[(0, 0), (300, 0), (750, -70), (1150, -25), (1550, -50), (1950, -75),
                 (2300, 0), (2500, 0)],
        aparicion=dict(
            total=50, min_vivos=3, max_vivos=9,
            intervalo_base=1.5, intervalo_por_vivo=0.3, reemplazo=0.4,
            etapas=[
                etapa(0.2, tipo("comun_chico", 2), tipo("comun_mediano", 1)),
                etapa(0.5, tipo("comun_chico", 2), tipo("comun_mediano", 2), tipo("corredor", 3)),
                etapa(1.0, tipo("comun_mediano", 3), tipo("corredor", 2), tipo("explosivo", 1),
                      tipo("comun_grande", 1), tipo("explosivo", 1, desde="dificil"),
                      tipo("acorazado", 1, desde="experto")),     # adelanto del nivel 3
            ],
            fijos=[
                fijo(0.2, [("corredor", 6)]),                         # primera estampida
                fijo(0.5, [("explosivo", 1), ("comun_chico", 4)]),    # el primer explosivo
                fijo(0.8, [("corredor", 10)], desde="dificil"),       # gran estampida
                fijo(0.9, [("acorazado", 1), ("comun_mediano", 2)], desde="experto"),
            ],
        ),
    ),
    dict(
        id="nivel3",
        nombre="Las Montañas",
        descripcion="Algunos invasores aprendieron a volar y a saltar. Usá las rocas sueltas de las cumbres.",
        posicion=(640, 300),
        disponible=True,
        ancho=2500,
        fondo="montanias",
        barriles=[1200, 1850],
        rocas=[750, 1650, 2050],  # posición x de cada roca suelta (en las cumbres)
        suelos=[(400, 680, "hielo"), (1280, 1560, "hielo")],
        terreno=[(0, 0), (300, 0), (750, -80), (1200, -30), (1650, -80), (2050, -40),
                 (2300, 0), (2500, 0)],
        aparicion=dict(
            total=55, min_vivos=3, max_vivos=9,
            intervalo_base=1.4, intervalo_por_vivo=0.3, reemplazo=0.4,
            etapas=[
                etapa(0.2, tipo("comun_mediano", 2), tipo("corredor", 2), tipo("volador_chico", 2)),
                etapa(0.55, tipo("comun_mediano", 2), tipo("corredor", 1), tipo("volador_chico", 2),
                      tipo("saltarin", 2), tipo("corredor_volador", 2), tipo("acorazado", 1)),
                etapa(1.0, tipo("comun_mediano", 1), tipo("volador_chico", 1), tipo("saltarin", 2),
                      tipo("corredor_volador", 2), tipo("acorazado", 1), tipo("volador_mediano", 2),
                      tipo("divisor", 2), tipo("explosivo", 1), tipo("comun_grande", 1),
                      tipo("divisor", 1, desde="dificil"), tipo("volador_mediano", 1, desde="dificil")),
            ],
            fijos=[
                fijo(0.15, [("volador_chico", 4)]),                              # primera bandada
                fijo(0.45, [("saltarin", 2), ("divisor", 1)]),
                fijo(0.6, [("chaman", 1), ("comun_mediano", 2)], desde="experto"),  # adelanto del nivel 4
                fijo(0.8, [("volador_mediano", 2), ("corredor_volador", 4)]),     # escuadrilla
                fijo(0.9, [("divisor", 3)], desde="dificil"),
            ],
        ),
    ),
    dict(
        id="nivel4",
        nombre="La Fortaleza",
        descripcion="El último bastión, con el jefe al final. "
                    "Estrellá enemigos contra los cristales para ganar energía.",
        posicion=(860, 220),
        disponible=True,
        ancho=2500,
        fondo="atardecer",
        barriles=[600, 1250],
        cristales=[900, 2000],   # posición x de cada cristal de energía
        suelos=[(700, 1000, "barro"), (1430, 1680, "hielo")],
        # Meseta larga en el medio (buena para muros)
        terreno=[(0, 0), (300, 0), (650, -60), (1350, -60), (1700, -20), (2000, -55),
                 (2300, 0), (2500, 0)],
        aparicion=dict(
            total=65, min_vivos=3, max_vivos=10,
            intervalo_base=1.3, intervalo_por_vivo=0.3, reemplazo=0.4,
            etapas=[
                etapa(0.25, tipo("comun_mediano", 2), tipo("corredor", 2), tipo("volador_chico", 2),
                      tipo("saltarin", 1), tipo("chaman", 1)),
                etapa(0.6, tipo("comun_mediano", 2), tipo("corredor", 1), tipo("volador_chico", 1),
                      tipo("corredor_volador", 1), tipo("saltarin", 1), tipo("chaman", 1),
                      tipo("animador", 1), tipo("acorazado", 1), tipo("divisor", 1), tipo("explosivo", 1)),
                etapa(1.0, tipo("comun_mediano", 1), tipo("comun_grande", 1), tipo("volador_mediano", 1),
                      tipo("corredor_volador", 1), tipo("saltarin", 1), tipo("chaman", 1),
                      tipo("animador", 1), tipo("acorazado", 2), tipo("divisor", 1), tipo("explosivo", 1),
                      tipo("acorazado", 1, desde="dificil"), tipo("animador", 1, desde="dificil")),
            ],
            fijos=[
                fijo(0.2, [("chaman", 1), ("comun_mediano", 3)]),     # el primer chamán
                fijo(0.45, [("animador", 1), ("corredor", 6)]),       # estampida acelerada
                fijo(0.7, [("acorazado", 2), ("chaman", 1)]),
                # Final (en=1.0): los grupos finales se juntan en este orden y son lo último que
                # aparece: la escolta (más grande en Difícil y Experto) y después el jefe
                fijo(1.0, [("chaman", 1)], desde="experto"),
                fijo(1.0, [("animador", 1)], desde="dificil"),
                fijo(1.0, [("comun_chico", 4), ("jefe", 1)]),
            ],
        ),
    ),
]

# Nivel de prueba (solo con C.DEBUG = True): copia de La Pradera, sin enemigos
# automáticos y sin victoria. No cuenta para el progreso.
NIVEL_PRUEBA = dict(
    id="prueba",
    nombre="Nivel de prueba",
    descripcion="Para probar enemigos, poderes y física.",
    posicion=(0, 0),
    disponible=True,
    prueba=True,
    ancho=2500,
    fondo="pradera",
    barriles=[700, 1250],
    rocas=[1100],
    cristales=[1750],
    suelos=[(850, 1050, "barro"), (1350, 1600, "hielo")],
    terreno=NIVELES[0]["terreno"],
    aparicion=None,
)

NIVELES_POR_ID = {n["id"]: n for n in NIVELES + [NIVEL_PRUEBA]}

# Requisitos de cada estrella (se muestran en la pantalla del nivel)
REQUISITOS_ESTRELLAS = [
    "Ganar el nivel",
    "Ganar con la base a más de la mitad",
    "Ganar sin perder ninguna vida",
    "Ganar en Difícil",
    "Ganar en Experto",
]


def siguiente_nivel(id_nivel):
    ids = [n["id"] for n in NIVELES]
    i = ids.index(id_nivel)
    return ids[i + 1] if i + 1 < len(ids) else None

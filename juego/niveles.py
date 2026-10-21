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
        barriles=[700, 1400],     # posición x de cada barril al empezar
        # Colinas: (x, desnivel). Negativo = más alto. Cerca de la base y de la entrada, plano.
        terreno=[(0, 0), (250, 0), (450, -45), (650, -65), (850, -20), (1050, 0), (1250, -55),
                 (1450, -85), (1650, -40), (1850, 10), (2050, -30), (2250, 0), (2500, 0)],
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
        barriles=[600, 1200, 1900],
        terreno=[(0, 0), (250, 0), (430, -50), (580, -90), (760, -100), (960, -40), (1120, 5),
                 (1300, -40), (1520, -100), (1700, -110), (1900, -50), (2080, 0), (2250, -20), (2500, -20)],
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
    dict(id="nivel3", nombre="Próximamente", descripcion="", posicion=(640, 300),
         disponible=False, barriles=[], aparicion=None),
    dict(id="nivel4", nombre="Próximamente", descripcion="", posicion=(860, 220),
         disponible=False, barriles=[], aparicion=None),
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
    barriles=[700, 1400],
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

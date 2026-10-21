# juego/config.py
# Constantes del juego en un solo lugar, para ajustar la "sensación" fácilmente.

ANCHO, ALTO = 1000, 600
FPS = 60
TITULO = "Juego con Físicas 2D"

SUELO_Y = 540
GROSOR_SUELO = 4
BASE_X = 70
GRAVEDAD = 900

# Modo desarrollo: muestra el nivel de prueba y habilita F1/F2/F3.
# Para la entrega poner en False.
DEBUG = True

# Colisiones
TIPO_ENEMIGO = 1
TIPO_BLOQUE = 2

# Daño por impacto
UMBRAL_IMPACTO = 450      # cambio de velocidad (px/s) a partir del cual duele
FACTOR_DANIO = 0.08       # daño por cada px/s por encima del umbral
DANIO_MINIMO = 5          # un choque que haría menos daño que esto no hace nada
VELOCIDAD_MINIMA_CHOQUE = 200  # px/s: si se acercaban más despacio, no cuenta como golpe
INVULNERABLE_CHOQUE = 0.15  # segundos sin recibir daño por choques después de un golpe

# Reglas de la partida
VIDAS_BASE = 5
TIEMPO_COMBO = 2.5                # segundos para encadenar eliminaciones
SEPARACION_GRUPO = (0.25, 0.6)    # segundos entre enemigos de un mismo grupo (al azar)

# Entrada de los enemigos: aparecen por el borde derecho lanzados, cayendo.
ENTRADA_ALTURA = (100, 260)       # px por encima del suelo
ENTRADA_VELOCIDAD_X = (150, 450)  # px/s hacia la izquierda (al azar)
ENTRADA_VELOCIDAD_Y = (-150, 50)  # px/s vertical (negativo = hacia arriba)
ENTRADA_SIN_DANIO = 1.5           # segundos sin daño por choques al entrar (para que la caída no los lastime)

# Dificultades: qué partes de la aparición se activan ("desde") y multiplicadores
#   cantidad:  multiplica el total de enemigos del nivel
#   vivos:     multiplica el mínimo y el máximo de enemigos vivos a la vez
#   reemplazo: se SUMA a la probabilidad de que entre otro al matar uno
#   ritmo:     divide el tiempo entre apariciones (más = más rápido)
DIFICULTADES = {
    "normal":  dict(nombre="Normal",  orden=0, cantidad=1.0,  vivos=1.0, reemplazo=0.0, ritmo=1.0),
    "dificil": dict(nombre="Difícil", orden=1, cantidad=1.25, vivos=1.2, reemplazo=0.2, ritmo=1.15),
    "experto": dict(nombre="Experto", orden=2, cantidad=1.5,  vivos=1.4, reemplazo=0.4, ritmo=1.3),
}

# Archivo donde se guarda el progreso (niveles desbloqueados, estrellas, volumen)
ARCHIVO_PROGRESO = "progreso.json"

# Enemigos
# radio/masa: tamaño y peso real en Pymunk
# vida, vel (px/s), ataque (daño por segundo a un bloque), puntos
# danio_base: corazones que le saca a tu base si llega
# pesado: reglas de enemigo grande (daño máximo por golpe, sigue caminando agarrado)
# valor_combo: cuántos eslabones de combo suma al eliminarlo
# agarre: aceleración con la que lo mueve la mano (más = más fácil de levantar y mover)
# lanzamiento: velocidad máxima con la que sale al soltarlo
# danio_base: vidas que le saca a tu base si llega
ENEMIGOS = {
    "comun_chico":   dict(nombre="Común chico", radio=14, masa=1, vida=30,  vel=95,  ataque=8,
                          puntos=10, danio_base=1, color=(70, 110, 170),
                          agarre=5200, lanzamiento=1600),
    "comun_mediano": dict(nombre="Común mediano", radio=21, masa=3, vida=60,  vel=65,  ataque=15,
                          puntos=25, danio_base=1, color=(150, 120, 40),
                          agarre=2281, lanzamiento=1151),
    "comun_grande":  dict(nombre="Común grande", radio=30, masa=8, vida=130, vel=40,  ataque=30,
                          puntos=60, danio_base=2, pesado=True, valor_combo=2, color=(160, 30, 50),
                          agarre=1093, lanzamiento=857),
    "corredor":      dict(nombre="Corredor", radio=11, masa=0.8, vida=20, vel=180, ataque=0,
                          puntos=15, danio_base=1, color=(60, 170, 90),
                          agarre=6147, lanzamiento=1711),
    "acorazado":     dict(nombre="Acorazado", radio=25, masa=6, vida=70,  vel=50,  ataque=20,
                          puntos=80, danio_base=2, pesado=True, valor_combo=3, color=(120, 90, 140),
                          # armadura: vida extra que hay que romper primero
                          # umbral/factor_armadura: daño por golpes según la fuerza total del choque
                          armadura=100, umbral_armadura=800, factor_armadura=0.015,
                          agarre=1356, lanzamiento=935),
    "explosivo":     dict(nombre="Explosivo", radio=19, masa=3, vida=40,  vel=45,  ataque=0,
                          puntos=40, danio_base=2, color=(200, 70, 30),
                          radio_explosion=110, fuerza_explosion=3000, danio_explosion=40,
                          agarre=2281, lanzamiento=1151),
}

# Barril explosivo (elemento de ayuda del mapa): se agarra y explota al chocarlo
# rápido contra un enemigo, solo si lo moviste vos. Es como una bomba, pero más fuerte.
BARRIL = dict(ancho=26, alto=34, masa=3, radio_explosion=160, fuerza=4500, danio=60,
              velocidad_explosion=450)   # explota si choca con un enemigo a esta velocidad o más,
                                         # solo si lo moviste vos (agarrado o lanzado)

# Bloques y materiales
TAM_BLOQUE = 30                 # lado de cada bloque en píxeles
FACTOR_DANIO_BLOQUE = 0.10      # daño por cada px/s de impacto por encima del umbral
# masa: peso real en Pymunk (cuesta más moverlo)
# vida: resistencia total
# umbral: cambio de velocidad mínimo para que un golpe lo dañe
MATERIALES = {
    "madera": dict(masa=2,  vida=60,  umbral=250, friccion=0.8, elasticidad=0.2, color=(150, 100, 50)),
    "piedra": dict(masa=6,  vida=150, umbral=300, friccion=0.9, elasticidad=0.1, color=(125, 125, 135)),
    "metal":  dict(masa=12, vida=300, umbral=350, friccion=0.6, elasticidad=0.1, color=(85, 100, 125)),
}

# Muro (después va a ser el poder "Construir")
MURO_COLUMNAS = 2
MURO_FILAS = 4
MURO_DURACION = 12              # segundos que dura antes de desaparecer
MURO_DANIO_SEPARA = 8           # los bloques del muro están unidos entre sí; un golpe que le haga
                                # a un bloque al menos este daño lo despega de sus vecinos

# Energía
ENERGIA_MAX = 100
ENERGIA_INICIAL = 40
ENERGIA_POR_ENEMIGO = 2         # energía por eliminar un enemigo suelto (primer eslabón)
ENERGIA_POR_ESLABON = 3         # cada eslabón del combo da esto × su número (x2 = 6, x3 = 9...)

# Caminata (los enemigos caminan con una fuerza limitada, no a velocidad fija)
CAMINAR_FUERZA = 900        # aceleración que se dan al caminar (× su masa): más pesados = empujan más
SALTO_PROBABILIDAD = 0.05   # probabilidad por cuadro de saltar cuando algo los bloquea adelante
SALTO_VELOCIDAD = 420       # impulso del salto (px/s)
SALTO_EMPUJE = 400          # empujoncito hacia adelante mientras suben en un salto
CALMA_LANZADO = 0.25        # segundos apoyado y a velocidad de caminata para dejar de contar como "lanzado"
FRENADO_LANZADO = 3.0       # qué tan rápido se frena un enemigo lanzado que rueda por el suelo

# Enemigos pesados (pesado=True en ENEMIGOS)
DANIO_MAXIMO_PESADO = 0.35      # ningún golpe les saca más que esta parte de su vida (o armadura) máxima
TIRON_PESADO = 1.0              # agarrados y tocando el suelo siguen caminando a esta parte de su velocidad (0 = no)

# Mano (mecánica base, no es un poder ni tiene niveles)
# La mano empuja lo que agarrás hacia el cursor con una aceleración máxima que baja
# con el peso: los pesados cuestan más de levantar, de mover y de lanzar.
# Los ENEMIGOS usan sus propios valores (agarre y lanzamiento en la tabla ENEMIGOS);
# esta fórmula general queda para bombas y barriles.
MANO_VEL_MAX = 1600            # velocidad máxima al lanzar algo de peso 1
MANO_ACELERACION = 5200        # aceleración máxima de la mano para algo de peso 1 (px/s²)
MANO_PESO_ACELERACION = 0.75   # cuánto baja la aceleración con el peso (0 = el peso no importa)
MANO_PESO_VELOCIDAD = 0.3      # cuánto baja la velocidad máxima de lanzamiento con el peso (0 = igual para todos)
MANO_SEGUIMIENTO = 16          # qué tan "decidida" va la mano hacia el cursor (más = más pegado)
MANO_VEL_SEGUIMIENTO = 3000    # velocidad máxima con la que la mano intenta llevarlo al cursor
CUERDA_LARGO_MAXIMO = 400      # si el cursor se aleja más que esto de lo agarrado, la "cuerda" se corta

# Poderes: cada uno tiene 3 niveles. El costo es el mismo en todos los niveles;
# lo que mejora es el efecto. Solo el rayo tiene "recarga" (cooldown).
PODERES = {
    "bomba": dict(nombre="Bomba", costo=20, niveles=[
        # mecha: segundos desde que la soltás / racimo: suelta 3 bombas chicas al explotar
        dict(mecha=3.0, radio=100, fuerza=2800, danio=30, racimo=False),
        dict(mecha=3.0, radio=130, fuerza=3500, danio=40, racimo=False),
        dict(mecha=3.0, radio=130, fuerza=3500, danio=40, racimo=True),
    ]),
    "agujero": dict(nombre="Agujero", costo=30, niveles=[
        # fuerza: atracción (fija, así a los pesados les cuesta más)
        # danio_centro: daño por segundo a las que quedan pegadas al centro
        dict(radio=200, duracion=3.0, fuerza=6000, danio_centro=0),
        dict(radio=250, duracion=4.0, fuerza=7000, danio_centro=0),
        dict(radio=250, duracion=4.0, fuerza=7000, danio_centro=30),
    ]),
    "muro": dict(nombre="Muro", costo=25, niveles=[
        dict(material="madera"),
        dict(material="piedra"),
        dict(material="metal"),
    ]),
    "rayo": dict(nombre="Rayo", costo=50, recarga=20, niveles=[
        # saltos: a cuántos enemigos más pasa la electricidad
        # decaimiento: qué parte del daño conserva en cada salto
        dict(danio=120, saltos=3, decaimiento=0.75, dist_salto=170, paralisis=1.0),
        dict(danio=120, saltos=5, decaimiento=0.75, dist_salto=170, paralisis=1.0),
        dict(danio=120, saltos=7, decaimiento=0.85, dist_salto=170, paralisis=1.0),
    ]),
}
ORDEN_PODERES = ["bomba", "agujero", "muro", "rayo"]   # teclas 1, 2, 3, 4
# Niveles con los que arranca la partida (después los va a dar la pantalla de mejoras)
NIVELES_INICIALES = {"bomba": 1, "agujero": 1, "muro": 1, "rayo": 1}

# Detalles visuales ("game feel")
TEMBLOR_EXPLOSION = 9       # píxeles de sacudida en explosiones
TEMBLOR_RAYO = 7
TEMBLOR_BASE = 6            # cuando la base pierde vida
TEMBLOR_GOLPE_MAX = 5       # golpes fuertes (escala con la fuerza)
TEMBLOR_AMORTIGUACION = 0.85  # cuánto se conserva de un frame al siguiente
POLVO_DELTA_V = 600         # cambio de velocidad mínimo para levantar polvo / sacudir
ZONA_PELIGRO = 300          # px delante de la base: si hay un enemigo ahí, se considera "cerca"
CONGELADO_FRAMES = 3        # congelado de impacto: cuadros que se detiene el mundo (0 = apagado)
CONGELADO_DELTA_V = 1100    # golpe mínimo (cambio de velocidad) que lo provoca
CONGELADO_ESPERA = 0.3      # segundos mínimos entre dos congelados
DESTELLO_DURACION = 0.08    # destello blanco al recibir daño (0 = apagado)
DESTELLO_DANIO_MIN = 3      # daño mínimo de un golpe para que destelle
ESTELA_VELOCIDAD = 700      # velocidad (px/s) a partir de la cual se deja estela (0 = apagado)
ESTELA_LARGO = 6            # cuántas "copias" forman la estela
CAMARA_LENTA_ESCALA = 0.3   # velocidad del mundo en la cámara lenta final
CAMARA_LENTA_DURACION = 1.0  # segundos reales que dura

# Mundo y cámara
ANCHO_MUNDO = 2500          # ancho por defecto del nivel (cada nivel puede definir el suyo)
CAMARA_VELOCIDAD = 800      # px/s al moverla con A/D o flechas
ARRASTRE_UMBRAL = 6         # px que hay que mover con clic derecho para que sea arrastre

# Colores
COLOR_CIELO = (170, 205, 190)
COLOR_SUELO = (70, 90, 60)
COLOR_BASE = (110, 80, 50)
COLOR_TEXTO = (20, 20, 20)

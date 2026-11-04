# Chaotic Legacy — Documento de diseño

| | |
|---|---|
| **Materia** | Taller de Videojuegos 2D · UTU · 2026 |
| **Integrantes** | Joaquín Ortiz · Facundo Cabrera |
| **Género** | Defensa con física (agarrar y lanzar) |
| **Referencia** | *Slammings* (el ritmo y la mecánica de agarrar enemigos) |
| **Tecnología** | Python 3 · Pygame · Pymunk (física) · motor 2D desarrollado en el curso |
| **Repositorio** | https://github.com/joaquinortiz337/Taller_Videojuegos |
| **Fecha** | Noviembre de 2026 |

## 1. Concepto

El jugador defiende una torre ubicada a la izquierda del mapa. Los invasores entran por la derecha y avanzan hacia ella caminando, saltando o volando. El jugador los detiene **agarrándolos con el mouse y lanzándolos** contra el suelo, los muros o entre sí, y apoyándose en cuatro poderes que se pagan con energía.

- **Victoria:** eliminar a todos los enemigos del nivel.
- **Derrota:** que los enemigos que llegan a la torre le quiten todos sus corazones (5, 6 o 7 según la mejora comprada).

## 2. Controles

| Acción | Control |
|---|---|
| Agarrar y lanzar / usar el poder elegido | Clic izquierdo (mantener y soltar para lanzar) |
| Elegir o cancelar un poder | Teclas 1 a 4, o clic en su casilla |
| Cancelar el poder | Clic derecho corto |
| Mover la cámara | A / D, flechas, clic derecho + arrastrar, o clic en el minimapa |
| Pausa | P o Esc |

## 3. Mecánicas implementadas

**La Mano.** Es la mecánica base: no es un poder, no tiene niveles y siempre está disponible. Lleva lo agarrado hacia el cursor con una aceleración máxima que depende del peso, y la gravedad sigue actuando. Por eso un enemigo grande cuesta más de levantar, mover y lanzar. Si el cursor se aleja demasiado, la "cuerda" se corta y el objeto se suelta.

**Daño por impacto.** El daño depende de la física real del choque: `daño = (Δv − 450) × 0.08`, donde `Δv` es el impulso dividido por la masa. Los enemigos livianos sufren más y los pesados casi no se inmutan. Solo cuentan los golpes que provoca el jugador. Los enemigos pesados no reciben más del 35 % de su vida por golpe.

**Combos y energía.** Eliminar enemigos en una ventana de 2,5 s encadena eslabones. Cada eslabón da más energía que el anterior y multiplica los puntos. La energía (máximo 100) se gasta en los poderes.

**Poderes** (3 niveles cada uno; el costo es fijo y lo que mejora es el efecto):

| Poder | Costo | Efecto |
|---|---|---|
| Bomba | 20 | Aparece en la mano; explota 3 s después de soltarla. Nivel 2: más radio y fuerza. Nivel 3: suelta 3 minibombas. |
| Agujero | 30 | Atrae a los enemigos cercanos durante 3 o 4 s. Nivel 3: daña a los que quedan en el centro. Los acorazados son inmunes. |
| Muro | 25 | Muro temporal (12 s) de 2×4 bloques soldados. Madera, piedra o metal según el nivel. |
| Rayo | 50 | Daña al enemigo más cercano y salta en cadena a 3, 5 o 7 más, paralizándolos. Recarga de 20 s. |

**Elementos del mapa.**
- **Barril:** explota si el jugador lo lanza rápido contra un enemigo.
- **Roca** (nivel 3): pesada, pega 1,5 veces más fuerte, no explota y se reutiliza.
- **Cristal de energía** (nivel 4): fijo en el suelo. Al estrellarle un enemigo con fuerza, este recibe daño extra y el jugador gana energía.
- **Suelo especial:** el barro frena a los enemigos a la mitad; el hielo los hace patinar y los acelera.

**Base.** La torre se agrieta, pierde almenas y echa humo al perder corazones. Los pobladores corren a refugiarse cuando sube el peligro. Las mejoras de la base agregan una torrecita y refuerzos de metal.

## 4. Enemigos (14 tipos)

| Tipo | Comportamiento |
|---|---|
| Común (chico, mediano, grande) | Camina y ataca los muros. El grande es pesado. |
| Corredor | Rápido y débil; no ataca muros. |
| Acorazado | Armadura extra: no se puede agarrar, es inmune al agujero y destruye bloques al contacto. Solo lo dañan enemigos, bombas y rocas lanzados. |
| Explosivo | Explota al morir o al tocar un muro. |
| Volador (3 variantes) | Vuela por encima de los muros. Si lo soltás fuerte, cae; si lo soltás flojo, planea y retoma el vuelo. |
| Saltarín | Avanza a saltos y pasa por encima de los muros. |
| Divisor | Al morir se parte en dos corredores. |
| Chamán | Cura a los enemigos heridos cercanos. |
| Animador | Acelera a los enemigos cercanos durante unos segundos. |
| Jefe | 400 de vida; su pisotón daña y empuja los muros y levanta a los demás enemigos. |

## 5. Niveles, dificultad y progresión

| Nivel | Enemigos (Normal) | Novedades |
|---|---|---|
| 1. La Pradera | 40 | Enemigos comunes; barriles; un tramo de barro. |
| 2. El Bosque | 50 | Corredores y explosivos; más barro. |
| 3. Las Montañas | 55 | Voladores, saltarines y divisores; rocas; hielo. |
| 4. La Fortaleza | 65 | Chamán, animador, acorazados y jefe final; cristales. |

- **Dificultades:** Normal, Difícil (+25 % de enemigos) y Experto (+50 %). Además suben la cantidad de enemigos vivos a la vez y el ritmo de aparición.
- **Estrellas (5 por nivel):** ganar; ganar con la base por encima de la mitad; ganar sin perder corazones; ganar en Difícil; ganar en Experto.
- **Mejoras:** las estrellas se gastan en subir los poderes y la base (2 estrellas el nivel 2, 3 el nivel 3). El máximo posible es 20 estrellas y mejorar todo cuesta 25, por lo que hay que elegir.
- **Guardado:** el avance (niveles, estrellas, mejoras y volúmenes) se guarda en `progreso.json`.

## 6. Decisiones de jugabilidad

1. **Que el peso se sienta.** Agarrar un enemigo debe tener resistencia física, y por eso la mano tiene aceleración limitada y la gravedad actúa siempre.
2. **Que solo cuente lo que hace el jugador.** Los enemigos no se lastiman al entrar, al saltar ni al amontonarse, de modo que el daño recompensa la habilidad y no el azar. Entran con 1,5 s de invulnerabilidad para que la caída inicial no los dañe.
3. **Un ciclo claro:** lanzar, encadenar combos, ganar energía, usar un poder.
4. **Enemigos que obligan a cambiar de táctica.** El acorazado exige bombas o rocas, los voladores ignoran los muros, el explosivo castiga atacarlo en mal lugar, y el chamán y el animador convierten en prioridad a un objetivo concreto.
5. **Un poder fuerte con recarga.** Solo el rayo tiene recarga, porque es el más poderoso. Los demás se limitan por energía.
6. **Dificultad por cantidad y ritmo, no por estadísticas.** Los enemigos son los mismos y solo cambia cuántos hay y qué tan rápido llegan.
7. **Decisiones de progresión.** Las estrellas alcanzan para 4 de las 5 mejoras al máximo, lo que obliga a elegir una especialización.
8. **Información clara bajo presión.** Hay flechas para enemigos fuera de pantalla, un minimapa, una alarma y un aviso en la zona de peligro, el contador "Quedan N", una barra de vida del jefe y un borde rojo al perder vida.
9. **Peligro dinámico.** Un valor de 0 a 1 (cercanía del enemigo más próximo, corazones perdidos y cantidad de enemigos) controla la música, el latido de la última vida, el borde rojo y el comportamiento de los pobladores.
10. **Enseñar de a poco.** Cada nivel agrega algo nuevo (rocas en el 3, cristales en el 4, barro y hielo), y el nivel 1 solo presenta la mecánica básica.

## 7. Audio y feedback

- **Efectos de impacto:** temblor de pantalla, partículas, congelado de unos cuadros en golpes fuertes, destello blanco al dañar, estelas en objetos rápidos y cámara lenta al ganar.
- **Música adaptativa:** tres capas sincronizadas (base, tensión, percusión) cuyo volumen sube o baja con el peligro.
- **Narrador:** frases cortas que reaccionan a combos, jefe, última vida y victoria. La música baja de volumen mientras habla.

## 8. Assets utilizados y su origen

El juego no utiliza imágenes, sonidos ni música de terceros. Todo se genera por código o es propio, con excepción de las fuentes y librerías.

| Tipo | Contenido | Origen | Licencia |
|---|---|---|---|
| Gráficos | Enemigos, torre, personas, bloques, fondos, interfaz, cursores | Dibujados por código con `pygame.draw`; no hay archivos de imagen | Propios |
| Efectos de sonido | 33 archivos `.wav` en `assets/sounds/` (golpes, explosión, rayo, combos, crujidos, alarma, latido, jingles, etc.) | Sintetizados con `tools/generar_sonidos.py` (ondas, ruido filtrado y envolventes, con numpy) | Propios |
| Música | 4 archivos `.wav` en `assets/music/`: `menu` y las tres capas de `partida` | Sintetizada con `tools/generar_musica.py` | Propia |
| Voz del narrador | 13 frases en inglés, `.wav` en `assets/sounds/voz/` | Voz de Joaquín Ortiz (integrante del equipo) | Propia |
| Tipografía principal | **Lilita One** (`assets/fonts/LilitaOne-Regular.ttf`), © 2011 Juan Montoreano | Fuente libre (disponible en Google Fonts) | SIL Open Font License 1.1 (copia en `assets/fonts/LilitaOne-OFL.txt`) |
| Tipografía secundaria | **FreeSans** (GNU FreeFont) | Es la fuente por defecto incluida en Pygame | GPLv3 con excepción de fuentes |
| Motor | `engine/` (bucle, escenas, cámara, partículas, parallax, audio) | Desarrollado durante el curso | Material del curso |
| Librerías | Pygame / Pygame-CE (render, entrada, audio) · Pymunk 7 (física, sobre Chipmunk2D) | Instaladas con `pip` | LGPL 2.1 · MIT |

## 9. Estructura del proyecto

```
main.py                  Punto de entrada
engine/                  Motor 2D del curso
juego/                   Juego: config, niveles, enemigos, poderes, mano, base, HUD
juego/scenes/            Menús, selección de niveles, mejoras, partida, victoria y derrota
assets/                  Sonidos, voz, música y tipografía
tools/                   Generadores de sonidos y música
prototipo/               Primer prototipo del núcleo (agarrar y lanzar)
```

Todo el balance (vida, velocidad, daño, costos, materiales) vive en `juego/config.py`, y los niveles se definen como datos en `juego/niveles.py`.

## 10. Cómo ejecutarlo

Requisitos: Python 3 y las librerías de `requirements.txt`. Versiones de referencia: Pymunk 7.x (el código usa la API de la versión 7) y, en Python 3.14, `pygame-ce` en lugar de `pygame`.

```bash
pip install pymunk pygame-ce
python main.py
```

Para regenerar el audio (opcional, requiere `numpy`): `python tools/generar_sonidos.py` y `python tools/generar_musica.py`.

**Modo desarrollo.** Con `DEBUG = True` en `juego/config.py` se habilita un nivel de prueba (con panel para crear enemigos) y las teclas F1 a F3. En la versión entregada debe estar en `False`.

## 11. Estado y limitaciones conocidas

- Los gráficos son provisorios: están dibujados por código y no hay sprites artísticos.
- Faltan cinco frases del narrador (`watch_out`, `amazing`, `incredible`, `armor_down` y `here_comes_the_boss`). El juego funciona igual, pero los avisos de armadura rota y de jefe no tienen voz.
- No hay pruebas automáticas: el balance y la física se validaron jugando, con el nivel de prueba.
- La simulación usa un paso de tiempo fijo de 1/60 s: si la máquina no sostiene los 60 FPS, el juego se ve más lento.

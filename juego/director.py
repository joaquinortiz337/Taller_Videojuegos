# juego/director.py
import random

from juego import config as C


class Director:
    """
    Decide QUÉ enemigos aparecen y CUÁNDO (ritmo inspirado en Slammings):
      - Cada nivel tiene un total de enemigos; se gana al eliminarlos a todos.
      - Hay un mínimo y un máximo de enemigos vivos a la vez.
      - El tiempo entre apariciones crece con la cantidad de vivos (se regula solo).
      - Al matar uno, hay una probabilidad de que entre otro al instante (rachas).
      - Qué tipos aparecen depende de cuánto del nivel ya pasó ("etapas"), y hay
        apariciones fijas en momentos concretos (el primer grande, una estampida...).
    """

    def __init__(self, nivel, dificultad):
        self.dif = C.DIFICULTADES[dificultad]
        orden = self.dif["orden"]
        self._permitido = lambda d: C.DIFICULTADES[d]["orden"] <= orden

        ap = nivel.get("aparicion")
        self.activo = ap is not None
        if not self.activo:          # nivel de prueba: no aparece nadie solo
            self.total = 0
            self.aparecidos = 0
            self.cola = []
            return

        d = self.dif
        self.total = max(1, round(ap["total"] * d["cantidad"]))
        self.min_vivos = round(ap["min_vivos"] * d["vivos"])
        self.max_vivos = max(1, round(ap["max_vivos"] * d["vivos"]))
        self.intervalo_base = ap["intervalo_base"] / d["ritmo"]
        self.intervalo_por_vivo = ap["intervalo_por_vivo"] / d["ritmo"]
        self.reemplazo = min(1.0, ap["reemplazo"] + d["reemplazo"])
        self.etapas = ap["etapas"]

        # Apariciones fijas: se convierten de "parte del nivel" (0 a 1) a número de enemigo
        # Los grupos con en=1.0 forman el FINAL: se juntan (en el orden en que están escritos)
        # y se ubican para ser lo último que aparece, enteros y sin mezclar (ej: escolta y jefe)
        self.fijos = {}
        permitidos = [f for f in ap["fijos"] if self._permitido(f["desde"])]
        final = [par for f in permitidos if f["en"] >= 1.0 for par in f["enemigos"]]
        if final:
            self.fijos[max(0, self.total - sum(n for _, n in final))] = (final, False)
        for f in permitidos:
            if f["en"] >= 1.0:
                continue
            indice = min(self.total - 1, round(f["en"] * self.total))
            while indice in self.fijos:
                indice += 1
            self.fijos[indice] = (f["enemigos"], True)   # (enemigos, mezclar)

        self.aparecidos = 0
        self.cola = []               # [segundos de espera, clave] ya decididos
        self.espera = 1.5            # primer enemigo a los 1,5 s
        self.reemplazo_pendiente = False

    # ---------- Estado ----------
    @property
    def terminado(self):
        """True cuando ya no va a aparecer ningún enemigo más."""
        return self.aparecidos >= self.total and not self.cola

    @property
    def progreso(self):
        return self.aparecidos / self.total if self.total else 1.0

    def quedan(self, vivos):
        """Enemigos que faltan eliminar: los que no aparecieron + los vivos."""
        return self.total - self.aparecidos + len(self.cola) + vivos

    # ---------- Eventos ----------
    def enemigo_eliminado(self, vivos):
        """La escena avisa que murió uno: puede entrar otro al instante."""
        if not self.activo or self.aparecidos >= self.total or vivos >= self.max_vivos:
            return
        if vivos < self.min_vivos or random.random() < self.reemplazo:
            self.reemplazo_pendiente = True

    # ---------- Lógica ----------
    def _elegir_tipo(self):
        prog = self.aparecidos / self.total
        etapa = next((e for e in self.etapas if prog < e["hasta"]), self.etapas[-1])
        opciones = [t for t in etapa["tipos"] if self._permitido(t["desde"])]
        return random.choices([t["clave"] for t in opciones],
                              weights=[t["peso"] for t in opciones])[0]

    def _decidir_siguiente(self):
        """Agrega a la cola el próximo enemigo (o el grupo fijo que toque)."""
        # Un grupo fijo puede haber quedado "salteado" si otro grupo grande pasó por encima
        # de su número: se toma el primero que ya debería haber salido
        pendientes = [i for i in self.fijos if i <= self.aparecidos]
        if pendientes:
            enemigos, mezclar = self.fijos.pop(min(pendientes))
            lista = []
            for clave, cantidad in enemigos:
                lista += [clave] * cantidad
            if mezclar:
                random.shuffle(lista)
        else:
            lista = [self._elegir_tipo()]
        lista = lista[:self.total - self.aparecidos]
        espera = self.cola[-1][0] if self.cola else 0.0
        for clave in lista:
            self.cola.append([espera, clave])
            espera += random.uniform(*C.SEPARACION_GRUPO)
        self.aparecidos += len(lista)

    def update(self, dt, vivos):
        """Avanza el tiempo y devuelve la lista de enemigos que tienen que aparecer ahora."""
        if not self.activo:
            return []
        quedan_por_decidir = self.aparecidos < self.total
        if quedan_por_decidir and not self.cola:
            self.espera -= dt
            if self.reemplazo_pendiente or (self.espera <= 0 and vivos < self.max_vivos):
                self._decidir_siguiente()
                self.reemplazo_pendiente = False
                intervalo = self.intervalo_base + vivos * self.intervalo_por_vivo
                self.espera = intervalo * random.uniform(0.8, 1.2)
            elif self.espera <= 0:
                self.espera = 0.3   # hay demasiados vivos: reintenta en un rato

        nuevos = []
        for item in self.cola:
            item[0] -= dt
        while self.cola and self.cola[0][0] <= 0:
            nuevos.append(self.cola.pop(0)[1])
        return nuevos

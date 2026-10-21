"""
engine/timeline.py

Línea de tiempo para animar valores y disparar eventos en el tiempo.

Se usa en la clase 14 (animación avanzada): permite "coreografiar" una
animación por keyframes sin llenar el bucle de `if`/`elif`.
"""


def linear(t):
    return t


def ease_in(t):
    return t * t


def ease_out(t):
    return 1 - (1 - t) * (1 - t)


def ease_in_out(t):
    return t * t * (3 - 2 * t)


EASINGS = {
    "linear": linear,
    "ease_in": ease_in,
    "ease_out": ease_out,
    "ease_in_out": ease_in_out,
}


class TimelineEvent:
    def __init__(self, time, callback, repeat=False, loop_interval=None):
        self.time = time
        self.callback = callback
        self.repeat = repeat
        self.loop_interval = loop_interval or time
        self.fired = False

    def reset(self):
        self.fired = False


class Tween:
    """Interpola un atributo de un objeto entre dos valores en un rango de tiempo."""

    def __init__(self, obj, attr, start, end, start_time, end_time, easing=None):
        self.obj = obj
        self.attr = attr
        self.start = start
        self.end = end
        self.start_time = start_time
        self.end_time = end_time
        self.easing = easing or linear

    def apply(self, time):
        if time <= self.start_time:
            setattr(self.obj, self.attr, self.start)
        elif time >= self.end_time:
            setattr(self.obj, self.attr, self.end)
        else:
            p = (time - self.start_time) / (self.end_time - self.start_time)
            setattr(self.obj, self.attr, self.start + (self.end - self.start) * self.easing(p))


class Timeline:
    """
    Reloj central. Cada frame se llama a `update(dt)`.

    - `add_tween(...)` interpola atributos.
    - `add_event(t, callback)` dispara funciones en un instante.
    - Si `duration` está definido y `loop=True`, se repite sola.
    """

    def __init__(self, duration=None, loop=False):
        self.time = 0.0
        self.duration = duration
        self.loop = loop
        self.active = True
        self.events = []
        self.tweens = []

    def add_event(self, time, callback, repeat=False):
        self.events.append(TimelineEvent(time, callback, repeat))

    def add_tween(self, obj, attr, start, end, start_time, end_time, easing=None):
        self.tweens.append(Tween(obj, attr, start, end, start_time, end_time, easing))

    def update(self, dt):
        if not self.active:
            return
        self.time += dt

        for tween in self.tweens:
            tween.apply(self.time)

        for event in self.events:
            if event.repeat:
                if self.time >= event.time:
                    event.callback()
                    event.time += event.loop_interval
            elif not event.fired and self.time >= event.time:
                event.callback()
                event.fired = True

        if self.duration is not None and self.time >= self.duration:
            if self.loop:
                self.reset()
            else:
                self.active = False

    def reset(self):
        self.time = 0.0
        self.active = True
        for event in self.events:
            event.reset()

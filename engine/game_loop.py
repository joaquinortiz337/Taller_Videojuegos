"""
engine/game_loop.py

Aquí viven los dos "corazones" del motor:

- GameLoop: el bucle clásico. Se usa por herencia (enfoque Game Loop).
- Game: un GameLoop que además entiende de escenas (enfoque Game Scenes).

Los dos comparten el mismo bucle `run()`, la misma gestión de eventos y el
mismo manejo de ventana/clock. La diferencia es SOLO cómo se delega el
trabajo de cada frame.
"""

import pygame


class GameLoop:
    """
    Bucle principal del juego.

    Uso (enfoque Game Loop):
        class MiJuego(GameLoop):
            def __init__(self):
                super().__init__(800, 600, "Mi Juego", 60)

            def handle_specific_events(self, event): ...
            def update_game_logic(self): ...
            def draw_game_elements(self): ...

        MiJuego().run()
    """

    def __init__(self, screen_width=800, screen_height=600, title="Juego", fps=60):
        pygame.init()

        # La música/efectos necesitan el mixer. Si falla, seguimos sin audio.
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()
        except pygame.error:
            pass

        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.running = True

    # ------------------------------------------------------------------ #
    #  Bucle principal
    # ------------------------------------------------------------------ #
    def _handle_events(self):
        """Recoge los eventos, cierra si toca y los reparte."""
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            # Hook 1: un evento cada vez (estilo clásico de Pygame).
            self.handle_specific_events(event)
        # Hook 2: toda la lista de golpe (estilo escenas).
        self.handle_events(events)

    def _update(self):
        self.update_game_logic()

    def _draw(self):
        self.draw_game_elements()
        pygame.display.flip()

    def run(self):
        """Arranca el bucle. Sale cuando self.running es False."""
        self.running = True
        while self.running:
            self.clock.tick(self.fps)
            self._handle_events()
            self._update()
            self._draw()
        pygame.quit()

    # ------------------------------------------------------------------ #
    #  Hooks para las clases hijas
    # ------------------------------------------------------------------ #
    def handle_specific_events(self, event):
        """Se llama con CADA evento (enfoque Game Loop)."""
        pass

    def handle_events(self, events):
        """Se llama con la LISTA de eventos (enfoque Game Scenes)."""
        pass

    def update_game_logic(self):
        """Actualiza la lógica del juego."""
        pass

    def draw_game_elements(self):
        """Dibuja el juego en self.screen."""
        pass


class Game(GameLoop):
    """
    GameLoop con gestor de escenas (enfoque Game Scenes).

    Las escenas se registran pasando la CLASE (no la instancia); el motor
    las instancia de nuevo cada vez que se entra a ellas. Así el estado se
    reinicia solo al volver al menú, empezar otra partida, etc.

    Uso:
        class MiJuego(Game):
            def __init__(self):
                super().__init__(800, 600, "Mi Juego", 60)
                self.add_scene("menu", MenuScene)
                self.add_scene("juego", JuegoScene)
                self.change_scene("menu")

        MiJuego().run()
    """

    def __init__(self, screen_width=800, screen_height=600, title="Juego", fps=60):
        super().__init__(screen_width, screen_height, title, fps)
        self.scenes = {}
        self.current_scene = None
        self._pending_scene = None  # (nombre, kwargs)

    # ------------------------------------------------------------------ #
    #  Registro y cambio de escenas
    # ------------------------------------------------------------------ #
    def add_scene(self, name, scene_class):
        """
        Registra una escena. `scene_class` debe ser una clase que herede de
        `engine.ui.Scene` y reciba el juego como primer argumento.
        """
        self.scenes[name] = scene_class

    def change_scene(self, name, **kwargs):
        """
        Pide cambiar de escena. El cambio se aplica de forma segura al
        principio de la siguiente actualización (no en medio del dibujado).
        """
        self._pending_scene = (name, kwargs)

    def _apply_pending_scene(self):
        if self._pending_scene is None:
            return

        name, kwargs = self._pending_scene
        self._pending_scene = None

        if self.current_scene is not None and hasattr(self.current_scene, "on_exit"):
            self.current_scene.on_exit()

        scene_class = self.scenes[name]
        self.current_scene = scene_class(self, **kwargs)

        if hasattr(self.current_scene, "on_enter"):
            self.current_scene.on_enter()

    # ------------------------------------------------------------------ #
    #  Delegación en la escena activa
    # ------------------------------------------------------------------ #
    def handle_events(self, events):
        if self.current_scene is not None:
            self.current_scene.handle_events(events)

    def update_game_logic(self):
        self._apply_pending_scene()
        if self.current_scene is not None:
            self.current_scene.update()

    def draw_game_elements(self):
        if self.current_scene is not None:
            self.current_scene.draw(self.screen)

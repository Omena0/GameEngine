from threading import Thread
from time import perf_counter
import pygame.gfxdraw
import pygame

from ..modules import shaders, draw
from ..classes import toast
from .. import constants


eventMap = {
    "keyDown": pygame.KEYDOWN,
    "keyUp": pygame.KEYUP,
    "mouseDown": pygame.MOUSEBUTTONDOWN,
    "mouseMove": pygame.MOUSEMOTION,
    "mouseUp": pygame.MOUSEBUTTONUP,
    "scroll": pygame.MOUSEWHEEL
}

class Game:
    __slots__ = ['id', 'version', 'title', 'size', 'width', 'height', 'res', 'max_fps',
                 'bg', 'sprites', 'toasts', 'spriteShaders', 'backgroundShaders', 'events',
                 'disp', 'clock', 'running', 'frame', 'dt', 'vsync', 'frameTime']

    VERSION: int = 0

    def __init__(self, title, size, res=16, max_fps=0, vsync=True, bg=(0,0,0), flags=0):
        # Make the active game reachable via `from engine import game` from anywhere.
        constants.game = self
        draw.game = self
        shaders.game = self
        toast.game = self

        self.title = title
        self.size = size
        self.width = size[0]//res
        self.height = size[1]//res
        self.res = res
        self.max_fps = max_fps
        self.vsync = vsync
        self.bg = bg
        self.frame = 0
        self.id = ''

        self.sprites = []
        self.toasts  = []
        self.spriteShaders = []
        self.backgroundShaders = []
        self.events  = {}

        self.disp = pygame.display.set_mode((self.width*res,self.height*res),vsync=vsync,flags=flags)
        self.clock = pygame.time.Clock()

        self.dt = 0.1
        self.frameTime = 0.1

    def _draw(self):  # sourcery skip: low-code-quality
        # Background shader pass
        if self.backgroundShaders:
            shader_surface = pygame.Surface((self.width, self.height))

            col = None

            # Shader pass
            for y in range(self.height):
                for x in range(self.width):
                    for shader in self.backgroundShaders:
                        col = shader(col, x, y, self.frame)
                        if col is None:
                            break

                    if col is not None:
                        shader_surface.set_at((x, y), col)

            self.width  = self.disp.get_width()  // self.res
            self.height = self.disp.get_height() // self.res

            # Scale shader surface to screen
            pygame.transform.scale(shader_surface, (self.width * self.res, self.height * self.res), self.disp)

        else:
            # Clear background
            self.disp.fill(self.bg)

        # Sprite rendering with culling
        screen_rect = pygame.Rect(0, 0, self.width, self.height)

        for sprite in self.sprites:
            if hasattr(sprite,'hidden') and sprite.hidden:
                continue

            # Custom draw method takes precedence
            if sprite.draw:
                sprite.draw()
                continue

            # Sprite culling
            sprite_rect = pygame.Rect(sprite.x, sprite.y, sprite.width, sprite.height)
            if not screen_rect.colliderect(sprite_rect):
                continue

            # Skip sprites outside screen bounds
            if not screen_rect.colliderect(sprite_rect):
                continue

            # Optimized sprite rendering
            for y in range(min(sprite.height, self.height - int(sprite.y))):
                for x in range(min(sprite.width, self.width - int(sprite.x))):
                    try:
                        col = sprite.texture[x][y]
                    except IndexError:
                        break

                    skip = False
                    # Apply shaders
                    for shader in self.spriteShaders:
                        col = shader(col, int(sprite.x + x), int(sprite.y + y), self.frame, sprite)
                        if not col:
                            skip = True
                            break

                    if skip:
                        break

                    # Draw pixel
                    pygame.gfxdraw.box(self.disp, ((sprite.x + x) * self.res, (sprite.y + y) * self.res, self.res, self.res), col)

    def _draw_toasts(self):
        removed = 0
        for toast in self.toasts.copy():
            toast._render()
            if toast.id <= -1:
                self.toasts.remove(toast)
                removed += 1

            toast.targetId -= removed
            if toast.targetId != toast.id:
                toast.id += (toast.targetId - toast.id) / 10

            if toast.animTarget >= 0:
                toast.animTarget -= min(toast.animTarget, 20)

    def shader(self, background = False):
        """
        Decorator that adds a shader callback to the rendering pipeline.

        Allows custom shader effects to be applied during rendering.

        Args: color, x, y, frame, sprite

        Returns:
            The original callback function, enabling decorator chaining.
        """
        def inner(callback):
            if background:
                self.backgroundShaders.append(callback)
            else:
                self.spriteShaders.append(callback)

            return callback
        return inner

    def on(self,action):
        def inner(callback):
            print(f'Registered Event: {action}')
            if action not in self.events:
                self.events[action] = []

            self.events[action].append(callback)

        return inner

    def run(self, callback=None):
        global dt

        self.running = True
        self.frame = 0

        if callback:
            Thread(target=callback).start()

        while self.running:
            start = perf_counter()
            events = pygame.event.get()

            # Event hooks
            if self.events.get('all'):
                for action,callbacks in self.events.items():
                    if action != 'all': continue
                    for callback in callbacks:
                        callback(events)

            # Event callbacks
            for event in events:
                for action,callbacks in self.events.copy().items():
                    if (event.type != eventMap.get(action) and eventMap.get(action) != "*"): continue

                    for callback in callbacks:
                        callback(event.dict)

                if event.type == pygame.QUIT:
                    self.running = False

            self._draw()

            for callback in self.events.get("frame",[]):
                callback(self.frame)

            self._draw_toasts()

            if self.frame % (10 if self.vsync else self.max_fps//8) == 0:
                pygame.display.set_caption(f'{self.title} FPS: {round(self.clock.get_fps(),2):5} FrameTime: {self.frameTime*1000:.1f} ms')

            pygame.display.flip()

            self.frame += 1

            self.frameTime = perf_counter() - start
            self.clock.tick(self.max_fps)
            self.dt = perf_counter() - start



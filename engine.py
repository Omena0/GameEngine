from typing import Callable, Any, Literal
from colorsys import hls_to_rgb
from numba import njit
import pygame.gfxdraw
import functools
import pygame
import types
import math
import json
import os

VERSION = 11

dt = 1

game = None

def cache(ignore=None) -> Callable:
    ignore = set() if ignore is None else set(ignore)
    def decorator(callback):
        _cache = {}

        @functools.wraps(callback)
        def wrapper(*args):
            # Avoid building tuple if no ignore — fast path
            if ignore:
                key = tuple(arg for i, arg in enumerate(args) if i not in ignore)
            else:
                key = args  # args is already a tuple, no need to rebuild

            if key not in _cache:
                _cache[key] = callback(*args)

            return _cache[key]

        return wrapper

    return decorator

pi        = math.pi
sin       = math.sin
cos       = math.cos
tan       = math.tan
sqrt      = math.sqrt
exp       = math.exp
atan2     = math.atan2
radians   = math.radians
log       = math.log

@njit
def hsl(h,s,l) -> tuple[int, int, int]:
    r,g,b = hls_to_rgb(h/360,l/100,s/100)
    return (int(r*255),int(g*255),int(b*255))

@njit
def distance(p1,p2) -> float:
    return sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)

def clamp(num, min_=0, max_=255) -> int:
    return min(max(num, min_), max_)

def clamp_ints(*args,min=0, max_=255) -> list[int]:
    return [clamp(int(num),min,max_) for num in args]

def sum_ints(*args) -> list[int]:
    result = [0]*len(args[0])
    for arg in args:
        for i,num in enumerate(arg):
            result[i] += num

    return result

fonts = {}
def getFont(size,bold=False,italic=False) -> Any | pygame.font.Font:
    if (size,bold,italic) in fonts:
        return fonts[size,bold,italic]

    font = pygame.font.SysFont('FreeSans',size)
    fonts[size,bold,italic] = font
    return font

def drawText(text: str, x: int, y: int, size=10, color=(255, 255, 255), bold=False, italic=False) -> None:
    font = getFont(size, bold, italic)
    screen_height = game.height * game.res
    screen_width = game.width * game.res + size

    for i, line in enumerate(text.splitlines()):
        if not line:
            continue

        render_y = y + size * i

        # Skip lines completely outside screen bounds
        if render_y >= screen_height or render_y + size < 0:
            continue

        # Efficient single-pass character rendering
        current_width = 0
        max_chars = len(line)
        for j, char in enumerate(line):
            char_width = textSize(char, size)[0]
            if current_width + char_width > screen_width:
                max_chars = j
                break
            current_width += char_width

        if truncated_line := line[:max_chars]:
            surf = font.render(truncated_line, True, color)
            game.disp.blit(surf, (x, render_y))

def drawRect(rect, color, width=0, border_radius=0) -> None:
    pygame.draw.rect(game.disp, color, rect, width, border_radius)

def drawLine(start, end, color, width=1) -> None:
    pygame.draw.line(game.disp, color, start, end, width)


### Shader Functions ###
def load_as_module(source, name, globals=None) -> types.ModuleType:
    # sourcery skip: avoid-builtin-shadow
    if globals is None:
        globals = {}
    module = types.ModuleType(name)
    module.__dict__.update(globals)
    exec(source, module.__dict__)
    return module

def loadShaderMeta(shader_pack) -> tuple[Literal['Error'], str] | Any:
    metapath = os.path.join(shader_pack, 'shader.json')

    with open(metapath) as f:
        meta = json.load(f)

    require = meta['require']

    if game.id in require:
        ver = require[game.id]
        try: compatible = ver == '*' or eval(f'{game.VERSION}{ver}')
        except: compatible = False
        if not compatible:
            return 'Error', f'This shader requires platformer version {ver}.'

    if 'engine' in require:
        ver = require['engine']
        try: compatible = ver == '*' or eval(f'{VERSION}{ver}')
        except: compatible = False
        if not compatible:
            return 'Error', f'This shader requires engine version {ver}.'

    return meta

def loadShaderFile(shader_pack, shader_file, globals=None):
    # sourcery skip: avoid-builtin-shadow
    if globals is None:
        globals = {}
    meta = loadShaderMeta(shader_pack)
    if isinstance(meta, tuple) and meta[0] == 'Error':
        return meta  # propagate error

    shader_meta = next((s for s in meta['shaders'] if s['filename'] == shader_file), None)

    if shader_meta.get('args'):
        if missing_args := [
            arg for arg in shader_meta['args'] if arg not in globals
        ]:
            return 'Error', f'Shader {shader_file} missing {len(missing_args)} arguments: {str(missing_args).strip("[]")}'

    with open(os.path.join(shader_pack, shader_file)) as f:
        try:
            module = load_as_module(f.read(), f.name, globals)
            shader_func = module.shader

            if shader_meta.get('cache', False):
                shader_func = cache(ignore=shader_meta.get('ignore_args', []))(shader_func)

            return shader_func

        except Exception as e:
            print(f'Error while loading shader {shader_file}: {e}')
            return

def loadShaders(shader_pack, shader_index=None):
    meta = loadShaderMeta(shader_pack)
    if not isinstance(meta, dict):
        return meta

    shaders = meta['shaders']

    if not shader_index:
        bg_shaders = []
        sprite_shaders = []

        for shader in shaders:
            if shader['type'] not in {'background','sprite'}:
                return 'Error', f'Unsupported shader type: {shader["type"]}'

            shader_func, cache = loadShaderFile(shader_pack, shader['filename'])

            if shader['type'] == 'background':
                bg_shaders.append((shader_func, cache))

            elif shader['type'] == 'sprite':
                sprite_shaders.append((shader_func, cache))

        return meta, bg_shaders, sprite_shaders

    shader = shaders[shader_index]

    if shader['type'] not in {'background','sprite'}:
        return 'Error', f'Unsupported shader type: {shader["type"]}'

    return loadShaderFile(shader_pack, shader['filename'])

def applyShader(surf, shader, res=4, mask=None, view_rect=None, args=None) -> pygame.Surface:
    """
        Applies a shader to a surface.

        Args:
            surf: The surface to apply the shader to.
            shader: A function that takes a color and returns a modified color.
            res: The resolution of the shader application (default is 4).
            mask: A color to not shade. (wont be visible)
            view_rect: Optional (x, y, width, height) to limit shader processing to visible area
    """
    if args is None:
        args = []
    # Create a new surface with alpha support
    result_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)

    # Copy initial surface
    result_surf.blit(surf, (0, 0))

    # Determine bounds for processing
    if view_rect:
        # Only process the visible part of the surface
        min_x = max(0, view_rect[0])
        min_y = max(0, view_rect[1])
        max_x = min(surf.get_width(), view_rect[0] + view_rect[2])
        max_y = min(surf.get_height(), view_rect[1] + view_rect[3])
    else:
        # Process the entire surface if no view rect specified
        min_x, min_y = 0, 0
        max_x, max_y = surf.get_width(), surf.get_height()

    # Process only the pixels within bounds
    for y in range(min_y, max_y, res):
        for x in range(min_x, max_x, res):
            try:
                color = surf.get_at((x, y))

                # Always skip completely transparent pixels
                if color.a == 0:
                    continue

                # If using mask and this is a masked color, make it transparent
                if mask and color.r == mask[0] and color.g == mask[1] and color.b == mask[2]:
                    result_surf.set_at((x, y), (0, 0, 0, 0))
                    continue

                # Apply shader and update
                new_color = shader(color, x, y, game.frame, *args)

                if not new_color:
                    continue
                rect = (x, y, res, res)
                pygame.gfxdraw.box(result_surf, rect, new_color)

            except IndexError:
                continue  # Handle edge case errors

    return result_surf

def drawRectShaded(rect, shader, res=4, border_radius=0, args=None) -> None:
    """
    Draw a shaded rectangle with optional rounded corners.
    Uses efficient pygame blending for proper masking and better performance.

    Args:
        rect: The rectangle (x, y, width, height)
        shader: Shader function to apply
        res: Resolution of shader application (pixel size)
        border_radius: Radius for rounded corners
    """
    if args is None:
        args = []
    # Create a surface that matches the rectangle's dimensions
    width, height = rect[2], rect[3]

    # Check if the rect is visible on screen at all
    screen_width = game.width * game.res
    screen_height = game.height * game.res

    # Skip if completely out of bounds
    if (rect[0] + width < 0 or rect[0] >= screen_width or
        rect[1] + height < 0 or rect[1] >= screen_height):
        return

    # Create surface for the colored/shaded content
    shader_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    shader_surface.fill((100, 100, 100, 255))  # Fill with a neutral gray

    # Apply the shader - only to visible portion
    visible_rect = [
        max(0, -rect[0]),
        max(0, -rect[1]),
        min(width, screen_width - rect[0]) - max(0, -rect[0]),
        min(height, screen_height - rect[1]) - max(0, -rect[1])
    ]

    shader_surface = applyShader(shader_surface, shader, res, view_rect=visible_rect, args=args)

    # Create the mask surface for the shape
    mask_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    mask_surface.fill((0, 0, 0, 0))  # Start transparent

    # Draw the rounded rectangle onto the mask
    pygame.draw.rect(mask_surface, (255, 255, 255, 255),
                   (0, 0, width, height), 0, border_radius)

    # Create the final surface
    result_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    result_surface.fill((0, 0, 0, 0))  # Start transparent

    # Blit the shader surface using the mask as an alpha channel
    result_surface.blit(shader_surface, (0, 0))
    result_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    # Blit the final result to the game display
    game.disp.blit(result_surface, (rect[0], rect[1]))

@cache()
def textSize(text,size) -> tuple[int | Any, Any]:
    font = getFont(size)
    i = 0
    largestX = 0
    for line in text.splitlines():
        if line:
            w = font.render(line,1,(255,255,255)).get_width()
            if w > largestX:
                largestX = w
            i += 1.1
        else:
            i += 0.5

    return largestX, size*i

def floodfill(texture, pos, newColor, oldColor):
    if texture[pos[0]][pos[1]] != oldColor: return
    texture[pos[0]][pos[1]] = newColor

    if pos[0] > 0: floodfill(texture, (pos[0]-1, pos[1]), newColor, oldColor)
    if pos[0] < len(texture)-1: floodfill(texture, (pos[0]+1, pos[1]), newColor, oldColor)
    if pos[1] > 0: floodfill(texture, (pos[0], pos[1]-1), newColor, oldColor)
    if pos[1] < len(texture[0])-1: floodfill(texture, (pos[0], pos[1]+1), newColor, oldColor)

def keyPressed(key:str):# -> Any:
    return pygame.key.get_pressed()[eval(f'pygame.K_{key}')]

def modPressed(mod:str) -> int | Literal[False]:
    mods = pygame.key.get_mods()
    match mod.lower():
        case 'shift':
            return mods & pygame.KMOD_SHIFT
        case 'ctrl':
            return mods & pygame.KMOD_CTRL
        case 'alt':
            return mods & pygame.KMOD_ALT
        case 'meta':
            return mods & pygame.KMOD_META
        case 'caps':
            return mods & pygame.KMOD_CAPS
        case 'num':
            return mods & pygame.KMOD_NUM
        case _:
            return False

class Vec2:
    __slots__ = ['_x', '_y', 'length']
    def __init__(self,x,y):
        self._x = x
        self._y = y
        self.length = distance((0,0),(x,y))

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self.length = distance((0,0),(value,self.y))

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self.length = distance((0,0),(value,self.y))

    def normalize(self):
        if self.length == 0:
            return Vec2(0, 0)
        return Vec2(self.x / self.length, self.y / self.length)

    def __eq__(self,other):
        return self.x == other.x and self.y == other.y

    def __ne__(self,other):
        return self.x != other.x or self.y != other.y

    def __add__(self,other):
        return Vec2(self.x+other.x,self.y+other.y)

    def __sub__(self, other):
        return Vec2(self.x-other.x,self.y-other.y)

    def __mul__(self, scalar):
        return Vec2(self.x*scalar,self.y*scalar)

    def __truediv__(self, scalar):
        return Vec2(self.x/scalar,self.y/scalar)

    def __str__(self):
        return f'Vec2({self.x},{self.y})'

    def __len__(self):
        return 2

    def __getitem__(self, index):
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError

    def __round__(self, ndigits=None):
        if ndigits is not None:
            return Vec2(round(self.x, ndigits), round(self.y, ndigits))
        return Vec2(round(self.x), round(self.y))

    def clamp(self, minValue, maxValue):
        return Vec2(max(minValue, min(self.x, maxValue)), max(minValue, min(self.y, maxValue)))

    def draw(self,x,y):
        pygame.draw.line(game.disp,(255,0,0),(x,y),(x+self.x,y+self.y),2)

class Toast:
    __slots__ = ['pos', 'text', 'height', 'width', 'color', 'start_time', 'duration', 'id', 'targetId', 'animTarget']
    def __init__(self, pos, text, height=25, color=(255,255,255), duration=2500):
        self.pos = [*pos]
        self.text = text
        self.height = height
        self.width = textSize(text,height-5)[0]+8
        self.color = color
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.id = len(game.toasts)
        self.targetId = self.id
        self.animTarget = self.width+5

        game.toasts.append(self)

    def _render(self):
        remaining = pygame.time.get_ticks() - self.start_time
        if remaining > self.duration:
            self.targetId = -2

        pos = self.pos.copy()
        pos[0] += self.animTarget
        pos[1] -= (self.height+10) * self.id

        pos[0] -= self.width
        pos[1] -= self.height

        drawRect((*pos, self.width,self.height), (50,50,50), border_radius=self.height//4)
        drawText(self.text, pos[0]+4, pos[1], size=self.height-5, color=self.color)

        return False

class Sprite:
    def __init__(self, pos, texture, draw=None):
        self.pos = pos
        self.x = pos[0]
        self.y = pos[1]
        if texture:
            self.width = len(texture)
            self.height = len(texture[0])
        else:
            self.width = 0
            self.height = 0
        self.texture = texture
        self.draw = draw

    def setPos(self,x,y):
        self.pos = x,y

    def move(self, pos):
        self.x += pos[0]
        self.y += pos[1]
        self.pos = self.x, self.y

    def collides_with(self, sprites):
        if isinstance(sprites, list):
            return [sprite for sprite in sprites if self.collides_with(sprite)]

        if sprites == "edge":
            return (
                self.x < 0
                or self.y < 0
                or self.x + self.width > self.game.width
                or self.y-1 + self.height > self.game.height
            )

        return sprites if (
            self.x-1 + self.width > sprites.x
            and self.x+1 < sprites.x + sprites.width
            and self.y-1 + self.height > sprites.y
            and self.y+1 < sprites.y + sprites.height
        ) else None

    def collidepoint(self, point):
        self.pos = round(self.pos[0]), round(self.pos[1])

        return (
            point[0] in range(self.pos[0], self.pos[0]+self.width-1)
            and point[1] in range(self.pos[1], self.pos[1]+self.height-1)
        )

    def raycast(self, angle, distance=500):
        """
        Raycast from the sprite in the given direction

        Returns the distance to the first collision, or None if no collision is found
        """
        angle = math.radians(angle)
        dx = round(math.cos(angle))
        dy = round(math.sin(angle))
        x = self.x+self.width/2
        y = self.y+self.height/2

        for steps in range(distance):
            x += dx
            y += dy
            for sprite in self.game.sprites:
                if sprite != self and sprite.x <= x < sprite.x + sprite.width and sprite.y <= y < sprite.y + sprite.height:
                    return steps, sprite

        return None

    def updateTexture(self, texture):
        self.width = len(texture)
        self.height = len(texture[0])
        self.texture = texture

    def add(self, game):
        self.game = game
        game.sprites.append(self)
        return self

eventMap = {
    "keyDown": pygame.KEYDOWN,
    "keyUp": pygame.KEYUP,
    "mouseDown": pygame.MOUSEBUTTONDOWN,
    "mouseMove": pygame.MOUSEMOTION,
    "mouseUp": pygame.MOUSEBUTTONUP,
    "scroll": pygame.MOUSEWHEEL
}

class Game:
    __slots__ = ['id', 'version', 'title', 'size', 'width', 'height', 'res', 'max_fps', 'bg', 'sprites', 'toasts', 'spriteShaders', 'backgroundShaders', 'events', 'disp', 'clock', 'running', 'frame']

    def __init__(self, title, size, res=16, max_fps=0, bg=(0,0,0), flags=0):
        global game
        game = self

        self.title = title
        self.size = size
        self.width = size[0]//res
        self.height = size[1]//res
        self.res = res
        self.max_fps = max_fps
        self.bg = bg

        self.sprites = []
        self.toasts  = []
        self.spriteShaders = []
        self.backgroundShaders = []
        self.events  = {}

        self.disp = pygame.display.set_mode((self.width*res,self.height*res),vsync=True,flags=flags)
        self.clock = pygame.time.Clock()

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

                    # Apply shaders
                    for shader in self.spriteShaders:
                        col = shader(col, int(sprite.x + x), int(sprite.y + y), self.frame, sprite)
                        if not col:
                            return

                    # Draw pixel
                    pygame.gfxdraw.box(self.disp, ((sprite.x + x) * self.res, (sprite.y + y) * self.res, self.res, self.res), col)

        # Toast rendering
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

    def shader(self,background = False):
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
        print(f'Registered Event: {action}')
        def inner(callback):
            if action[0] not in self.events:
                self.events[action] = []

            self.events[action].append((callback))

        return inner

    def run(self, callback=None):
        global dt

        self.running = True
        self.frame = 0

        while self.running:
            if callback:
                callback(self.frame)

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

            if self.frame % 10 == 0:
                pygame.display.set_caption(f'{self.title} FPS: {round(self.clock.get_fps(),2)} FrameTime: {self.clock.get_rawtime()}')

            pygame.display.flip()

            self.frame += 1
            dt = self.clock.tick_busy_loop(self.max_fps)/1000

__all__ = ["hsl", "distance", "clamp", "clamp_ints", "getFont", "drawText", "textSize", "floodfill", "keyPressed", "modPressed", "cache", "Vec2", "Sprite", "Toast", "eventMap", "Game"]


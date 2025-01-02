from colorsys import hls_to_rgb
import pygame
import math

dt = 1

game = None

def cache(simple=True, ignored=None, periods=None, max_size=128):
    if not simple:
        def decorator(callback):
            _cache = {}

            def wrapper(*args, **kwargs):
                # Determine which arguments to ignore
                ignore_args = set(ignored) if isinstance(ignored, (list, set, tuple)) else set()
                ignore_kwargs = set(ignored) if isinstance(ignored, dict) else set()

                # Filter out ignored arguments
                filtered_args = tuple(
                    arg for i, arg in enumerate(args)
                    if i not in ignore_args
                )
                filtered_kwargs = {
                    k: v for k, v in kwargs.items()
                    if k not in ignore_kwargs
                }

                # Generate key with periods applied
                if periods:
                    key = []
                    for i, arg in enumerate(filtered_args):
                        if i in periods:
                            key.append(arg % periods[i])
                        else:
                            key.append(arg)

                    for k, v in sorted(filtered_kwargs.items()):
                        if k in periods:
                            key.append(v % periods[k])
                        else:
                            key.append(v)

                    key = tuple(key)
                else:
                    key = filtered_args + tuple(sorted(filtered_kwargs.items()))

                if key not in _cache:
                    _cache[key] = callback(*args, **kwargs)

                return _cache[key]
            return wrapper

    else:
        def decorator(callback):
            _cache = {}

            def wrapper(*args):
                # Use faster hash-based lookup for hashable arguments
                key = hash(args)

                if key not in _cache:
                    _cache[key] = callback(*args)

                return _cache[key]
            return wrapper
    return decorator

sin = math.sin
cos = math.cos
sqrt = math.sqrt

def exp(x):
    return math.exp(x)

def hsl(h,s,l):
    r,g,b = hls_to_rgb(h/360,l/100,s/100)
    return (int(r*255),int(g*255),int(b*255))

def distance(p1,p2):
    return sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)

def clamp(num, min_=0, max_=255):
    return min(max(num, min_), max_)

def clamp_ints(*args,min=0, max_=255):
    return [clamp(num,min,max_) for num in args]

fonts = {}
def getFont(size,bold=False,italic=False):
    if (size,bold,italic) in fonts:
        return fonts[size,bold,italic]

    font = pygame.font.SysFont('FreeSans',size)
    fonts[size,bold,italic] = font
    return font

def drawText(text: str, x: int, y: int, size=10, color=(255, 255, 255), bold=False, italic=False):
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

        truncated_line = line[:max_chars]

        if truncated_line:
            surf = font.render(truncated_line, True, color)
            game.disp.blit(surf, (x, render_y))

def drawRect(rect, color, width=0, border_radius=0):
    pygame.draw.rect(game.disp, color, rect, width, border_radius)

@cache()
def textSize(text,size):
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

def keyPressed(key:str):
    return pygame.key.get_pressed()[eval(f'pygame.K_{key}')]

def modPressed(mod:str):
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
            return Vec2(0,0)
        return Vec2(self.x/self.length,self.y/self.length)

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
        return Vec2(round(self.x), round(self.y),ndigits)

    def clamp(self,minValue,maxValue):
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
    def __init__(self, pos, texture, draw = None):
        self.pos = pos
        self.x = pos[0]
        self.y = pos[1]
        if texture:
            self.width = len(texture)+1
            self.height = len(texture[0])+1
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

    def updateTexture(self,texture):
        self.width = len(texture)+1
        self.height = len(texture[0])+1
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
    __slots__ = ['title', 'size', 'width', 'height', 'res', 'max_fps', 'bg', 'sprites', 'toasts', 'spriteShaders', 'backgroundShaders', 'events', 'disp', 'clock', 'running', 'frame']

    def __init__(self, title, size, res=16, max_fps=0, bg=(0,0,0), flags=0):
        global game
        game = self

        self.title = title
        self.size = size
        self.width = size[0]
        self.height = size[1]
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
        # Clear background
        if self.backgroundShaders:
            shader_surface = pygame.Surface((self.width, self.height))

            # Shader pass
            for y in range(self.height):
                for x in range(self.width):
                    col = self.bg
                    for shader in self.backgroundShaders:
                        col = shader(col, x, y, self.frame, None)
                        if col is None:
                            break

                    if col is not None:
                        shader_surface.set_at((x, y), col)

            # Scale shader surface to screen
            pygame.transform.scale(shader_surface, (self.width * self.res, self.height * self.res), self.disp)
        else:
            self.disp.fill(self.bg)

        # Sprite rendering with culling
        screen_rect = pygame.Rect(0, 0, self.width, self.height)

        for sprite in self.sprites:
            # Sprite culling
            sprite_rect = pygame.Rect(sprite.x, sprite.y, sprite.width, sprite.height)
            if not screen_rect.colliderect(sprite_rect):
                continue

            # Custom draw method takes precedence
            if sprite.draw:
                sprite.draw()
                continue

            # Skip sprites outside screen bounds
            if (sprite.x >= self.width or sprite.y >= self.height or 
                sprite.x + sprite.width < 0 or sprite.y + sprite.height < 0):
                continue

            # Optimized sprite rendering
            for y in range(max(0, -int(sprite.y)), min(sprite.height, int(self.height + 1 - sprite.y))):
                for x in range(max(0, -int(sprite.x)), min(sprite.width, int(self.width + 1 - sprite.x))):
                    try:
                        # Swap x and y to match typical texture format
                        col = sprite.texture[y][x]
                    except IndexError:
                        continue

                    # Apply shaders
                    for shader in self.spriteShaders:
                        col = shader(col, int(sprite.x + x), int(sprite.y + y), self.frame, sprite)
                        if not col:
                            return

                    # Draw pixel
                    pygame.draw.rect(self.disp, col, 
                        ((sprite.x + x) * self.res, (sprite.y + y) * self.res, self.res, self.res))

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



    def shader(self,callback):
        """
        Decorator that adds a shader callback to the rendering pipeline.

        Allows custom shader effects to be applied during rendering.

        Args: color, x, y, frame, sprite

        Returns:
            The original callback function, enabling decorator chaining.
        """
        self.spriteShaders.append(callback)
        return callback

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

            pygame.display.set_caption(f'{self.title} FPS: {round(self.clock.get_fps(),2)}')
            pygame.display.update()

            self.frame += 1
            dt = self.clock.tick(self.max_fps)/1000

__all__ = ["hsl", "distance", "clamp", "clamp_rbg", "getFont", "drawText", "textSize", "floodFill", "keyPressed", "modPressed", "cache", "Vec2", "Sprite", "Toast", "eventMap", "Game"]


import pygame
import math

dt = 1
game = None

def clamp(num, min_=0, max_=255):
    return min(max(num, min_), max_)

def clamp_rgb(col):
    return (clamp(col[0]), clamp(col[1]), clamp(col[2]))

fonts = {}
def getFont(size,bold=False,italic=False):
    if (size,bold,italic) in fonts:
        return fonts[size,bold,italic]

    font = pygame.font.SysFont('FreeSans',size)
    fonts[size,bold,italic] = font
    return font

def drawText(text:str,x:int,y:int,size=10,color=(255,255,255),bold=False,italic=False):
    font = getFont(size,bold,italic)
    i = 0
    for line in text.splitlines():
        if line:
            surf = font.render(line,1,color)
            game.screen.blit(surf,(x,y+size*i))
            i += 1.1
        else:
            i += 0.5

def drawRect(rect, color, width=0, border_radius=0):
    pygame.draw.rect(game.screen, color, rect, width, border_radius)

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


class Toast:
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
    def __init__(self, pos, texture, renderMethod = None):
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
        self.renderMethod = renderMethod

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
    def __init__(self, title, size, res=16, max_fps=0, bg=(0,0,0)):
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
        self.shaders = []
        self.events  = {}

        self.screen = pygame.display.set_mode((self.width*res,self.height*res),vsync=True)
        self.clock = pygame.time.Clock()

    def _draw(self):  # sourcery skip: low-code-quality
        col = self.bg

        # Shader pass
        if self.shaders:
            for y in range(self.size[1]):
                for x in range(self.size[0]):
                    for shader in self.shaders:
                        col = shader(col, x, y, self.frame, None)
                        if not col: return

                    pygame.draw.rect(self.screen, clamp_rgb(col), (x*self.res, y*self.res, self.res, self.res))

        # Clear bg
        else:
            self.screen.fill(col)

        # Sprites
        for sprite in self.sprites:
            if sprite.renderMethod:
                sprite.renderMethod()
                continue

            if sprite.x >= self.width or sprite.y >= self.height: continue
            if sprite.x+sprite.width < 0 or sprite.y+sprite.height < 0: continue
            for y in range(max(0, -int(sprite.y)), min(sprite.height-1, int(self.height+1-sprite.y))):
                for x in range(max(0, -int(sprite.x)), min(sprite.width-1, int(self.width+1-sprite.x))):

                    col = sprite.texture[x][y]

                    for shader in self.shaders:
                        col = shader(col, sprite.x+x, sprite.y+y, self.frame, sprite)
                        if not col: return

                    pygame.draw.rect(self.screen, clamp_rgb(col), ((sprite.x+x)*self.res, (sprite.y+y)*self.res, self.res, self.res))

        # Toast render
        removed = 0
        for toast in self.toasts.copy():
            toast._render()
            if toast.id <= -1:
                self.toasts.remove(toast)
                removed += 1

            toast.targetId -= removed
            if toast.targetId != toast.id:
                toast.id += (toast.targetId-toast.id)/10

            if toast.animTarget >= 0:
                toast.animTarget -= min(toast.animTarget, 20)

    def shader(self,callback):
        self.shaders.append(callback)

    def on(self,action):
        print(f'Registered Event: {action}')
        def inner(callback):
            if action[0] not in self.events:
                self.events[action] = []

            self.events[action].append((callback))

        return inner

    def run(self):
        global dt
        self.running = True
        self.frame = 0
        while self.running:
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




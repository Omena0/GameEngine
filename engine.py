import pygame
import math

def clamp(num, min_=0, max_=255):
    return min(max(num, min_), max_)

def clamp_rgb(col):
    return (clamp(col[0]), clamp(col[1]), clamp(col[2]))

class Sprite:
    def __init__(self, pos, texture):
        self.pos = pos
        self.x = pos[0]
        self.y = pos[1]
        self.width = len(texture)+1
        self.height = len(texture[0])+1
        self.texture = texture

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

events = {
    "keyDown": pygame.KEYDOWN,
    "keyUp": pygame.KEYUP,
    "mouseDown": pygame.MOUSEBUTTONDOWN,
    "mouseMove": pygame.MOUSEMOTION,
    "mouseUp": pygame.MOUSEBUTTONUP
}

class Game:
    def __init__(self, title, size, res=16, max_fps=0, bg=(0,0,0)):
        self.title = title
        self.size = size
        self.width = size[0]
        self.height = size[1]
        self.res = res
        self.max_fps = max_fps
        self.bg = bg

        self.sprites = []
        self.shaders = []
        self.events = {}

        self.use_shader_rendering = False

        self.screen = pygame.display.set_mode((self.width*res,self.height*res))
        self.clock = pygame.time.Clock()

    def _draw(self):
        col = self.bg

        if self.shaders:
            for y in range(self.size[1]):
                for x in range(self.size[0]):
                    for shader in self.shaders:
                        col = shader(col, x, y, self.frame, None)
                        if not col: return

                    pygame.draw.rect(self.screen, clamp_rgb(col), (x*self.res, y*self.res, self.res, self.res))

        else:
            self.screen.fill(col)

        for sprite in self.sprites:
            if sprite.x >= self.width or sprite.y >= self.height: continue
            if sprite.x+sprite.width < 0 or sprite.y+sprite.height < 0: continue
            for y in range(max(0, -int(sprite.y)), min(sprite.height-1, int(self.height+1-sprite.y))):
                for x in range(max(0, -int(sprite.x)), min(sprite.width-1, int(self.width+1-sprite.x))):

                    col = sprite.texture[x][y]

                    for shader in self.shaders:
                        col = shader(col, sprite.x+x, sprite.y+y, self.frame, sprite)
                        if not col: return

                    pygame.draw.rect(self.screen, clamp_rgb(col), ((sprite.x+x)*self.res, (sprite.y+y)*self.res, self.res, self.res))

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
        self.running = True
        self.frame = 0
        while self.running:
            for event in pygame.event.get():
                for action,callbacks in self.events.items():
                    for eventName, eventValue in events.items():
                        if action == eventName and event.type == eventValue:
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
            self.clock.tick(self.max_fps)




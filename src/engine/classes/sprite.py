import math


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
                or self.y + self.height > self.game.height
            )

        # Standard AABB overlap with a small resting tolerance so the
        # camera-follow velocity offset doesn't toggle onGround every frame
        # and re-apply gravity (causing the player to jitter/sink into floors).
        eps = 0.5
        return sprites if (
            self.x + self.width >= sprites.x - eps
            and self.x <= sprites.x + sprites.width + eps
            and self.y + self.height >= sprites.y - eps
            and self.y <= sprites.y + sprites.height + eps
        ) else None

    def collidepoint(self, point):

        pos = round(self.pos[0]), round(self.pos[1])

        return (
            point[0] in range(pos[0], pos[0]+self.width-1)
            and point[1] in range(pos[1], pos[1]+self.height-1)
        )

    def raycast(self, angle, distance=500):

        """
        Raycast from the sprite in the given direction

        Returns the distance to the first collision, or None if no collision is found
        """
        angle = math.radians(angle)
        dx = round(math.cos(angle))/2
        dy = round(math.sin(angle))/2
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



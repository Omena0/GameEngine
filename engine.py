import pygame

class Sprite:
    def __init__(self, pos, texture):
        self.pos = pos
        self.texture = texture

    def move(self, pos):
        self.pos = pos
    
    def add(self, game):
        self.game = game
        game.sprites.add(self)

class Game:
    def __init__(self, title, size, res=16, max_fps=0):
        self.title = title
        self.size = size
        self.res = res
        self.max_fps = max_fps

        self.regions = [set() for _ in range(16)]

        self.screen = pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()

    def _shader(self,x,y):
        # The entire window will be split into regions that each contain sprites.
        # Loop for each sprite in the region
        


        col = (0,0,0)
        pygame.draw.rect(self.screen, col, (x*self.res, y*self.res, self.res, self.res))

    def _draw(self):
        for y in range(self.size[0]//self.res):
            for x in range(self.size[1]//self.res):
                self._shader(x,y)

    def run(self):
        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()

            self._draw()

            pygame.display.set_caption(f'{self.title} FPS: {round(self.clock.get_fps(),2)}')
            pygame.display.update()

            self.clock.tick(self.max_fps)




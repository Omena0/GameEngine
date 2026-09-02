import pygame

from ..modules.draw import drawText, drawRect
from ..modules.utils import textSize
from .. import game

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

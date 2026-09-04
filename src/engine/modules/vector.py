import pygame

from ..modules.math import distance
from .. import game


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
        self.length = distance((0,0),(self.x, value))

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

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

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



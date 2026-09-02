from typing import Callable, Any
from ast import literal_eval
import pygame

fonts = {}
def getFont(size, bold=False, italic=False) -> pygame.font.Font:
    size = int(size * 1.5)
    key = (size, bold, italic)
    if key in fonts:
        return fonts[key]

    font = pygame.font.SysFont(None, size)
    fonts[key] = font
    return font

def cache(ignore=None) -> Callable:
    ignore = set() if ignore is None else set(ignore)
    def decorator(callback):
        _cache = {}

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


def convert_type(s):
    """Convert a string to its Python literal type if possible."""
    try:
        return literal_eval(s)
    except Exception:
        return s

@cache()
def textSize(text,size) -> tuple[int | Any, Any]:
    font = getFont(size)
    i = 0
    largestX = 0
    for line in text.splitlines():
        if line:
            w = font.size(line)[0]
            if w > largestX:
                largestX = w
            i += 1.1
        else:
            i += 0.5

    return largestX, size*i

def floodfill(texture, pos, newColor, oldColor):
    rows = len(texture)
    cols = len(texture[0]) if rows > 0 else 0
    stack = [pos]

    while stack:
        x, y = stack.pop()
        if texture[x][y] != oldColor or texture[x][y] == newColor:
            continue
        texture[x][y] = newColor

        if x > 0:
            stack.append((x-1, y))
        if x < rows-1:
            stack.append((x+1, y))
        if y > 0:
            stack.append((x, y-1))
        if y < cols-1:
            stack.append((x, y+1))


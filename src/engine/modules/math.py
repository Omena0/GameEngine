from colorsys import hls_to_rgb
from numba import njit
import math


pi        = math.pi
sin       = math.sin
cos       = math.cos
tan       = math.tan
sqrt      = math.sqrt
exp       = math.exp
atan2     = math.atan2
radians   = math.radians
log       = math.log

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

def round_ints(*args):
    return [round(i) for i in args]

__all__ = [
    # math funcs
    'pi',
    'sin',
    'cos',
    'tan',
    'sqrt',
    'exp',
    'atan2',
    'radians',
    'log',

    # specific
    'hsl',
    'distance',
    'clamp',

    # vector
    'clamp_ints',
    'sum_ints',
    'round_ints'
]



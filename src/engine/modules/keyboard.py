from typing import Literal
import pygame

def keyPressed(key:str):# -> Any:
    return pygame.key.get_pressed()[getattr(pygame, f'K_{key}')]

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

__all__ = [
    'keyPressed',
    'modPressed'
]

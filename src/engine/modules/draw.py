from typing import Any
import pygame

from ..modules.shaders import applyShader
from ..modules.utils import textSize, getFont
from .. import game


def drawText(text: str, x: int, y: int, size=10, color=(255, 255, 255), bold=False, italic=False, dest_surf=None) -> pygame.Surface:
    font = getFont(size, bold, italic)
    screen_height = game.height * game.res
    screen_width = game.width * game.res

    if not dest_surf:
        dest_surf = game.disp

    if dest_surf == 'new':
        dest_surf = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        dest_surf.fill((0,0,0,0))

    for i, line in enumerate(text.splitlines()):
        if not line:
            continue

        render_y = y + size * i

        # Skip lines completely outside screen bounds
        if render_y >= screen_height or render_y + size < 0:
            continue

        # Character-by-character horizontal culling
        char_x = x
        visible_chars = []
        visible_start_x = None

        for char in line:
            char_width = textSize(char, size)[0]
            char_end_x = char_x + char_width

            # Check if character is visible
            if char_end_x > 0 and char_x < screen_width:
                if visible_start_x is None:
                    visible_start_x = char_x
                visible_chars.append(char)
            elif char_x >= screen_width:
                # Past right edge, no more visible chars
                break

            char_x = char_end_x

        if visible_chars and visible_start_x is not None:
            visible_text = ''.join(visible_chars)
            surf = font.render(visible_text, True, color)
            dest_surf.blit(surf, (visible_start_x, render_y))

    return dest_surf

def drawRect(rect, color, width=0, border_radius=0) -> None:
    pygame.draw.rect(game.disp, color, rect, width, border_radius)

def drawLine(start, end, color, width=1) -> None:
    pygame.draw.line(game.disp, color, start, end, width)

## Shaded drawing primitives ##
def drawRectShaded(shader, rect, res=4, border_radius=0, args=None) -> None:
    """
    Draw a shaded rectangle with optional rounded corners.
    Uses efficient pygame blending for proper masking and better performance.

    Args:
        rect: The rectangle (x, y, width, height)
        shader: Shader function to apply
        res: Resolution of shader application (pixel size)
        border_radius: Radius for rounded corners
    """
    if args is None:
        args = []
    # Create a surface that matches the rectangle's dimensions
    width, height = rect[2], rect[3]

    # Check if the rect is visible on screen at all
    screen_width = game.width * game.res
    screen_height = game.height * game.res

    # Skip if completely out of bounds
    if (rect[0] + width < 0 or rect[0] >= screen_width or
        rect[1] + height < 0 or rect[1] >= screen_height):
        return

    # Create surface for the colored/shaded content
    shader_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    shader_surface.fill((0,0,0,255))  # Fill with black

    # Apply the shader - only to visible portion
    visible_rect = [
        max(0, -rect[0]),
        max(0, -rect[1]),
        min(width, screen_width - rect[0]) - max(0, -rect[0]),
        min(height, screen_height - rect[1]) - max(0, -rect[1])
    ]

    shader_surface = applyShader(shader_surface, shader, res, view_rect=visible_rect, args=args)

    # Create the mask surface for the shape
    mask_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    mask_surface.fill((0, 0, 0, 0))  # Start transparent

    # Draw the rounded rectangle onto the mask
    pygame.draw.rect(mask_surface, (255, 255, 255, 255),
                   (0, 0, width, height), 0, border_radius)

    # Create the final surface
    result_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    result_surface.fill((0, 0, 0, 0))  # Start transparent

    # Blit the shader surface using the mask as an alpha channel
    result_surface.blit(shader_surface, (0, 0))
    result_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    # Blit the final result to the game display
    game.disp.blit(result_surface, (rect[0], rect[1]))

def drawTextShaded(shader, text: str, x: int, y: int, size=10, bold=False, italic=False, res=1, args=None):
    """
    Draw shaded text.

    Args:
        shader: The shader function to use
        text: The text, can contain newlines.
        x: X position
        y: Y position
        size: Font size
        bold: Whether the text should be bold
        italic: Whether the text should be italic
    """
    if args is None:
        args = []

    # Draw mask
    shaded_surf = drawText(text, 0, 0, size, (255, 255, 255), bold, italic, 'new')
    shaded_surf = applyShader(shaded_surf, shader, 1, (0, 0, 0), args=args)

    game.disp.blit(shaded_surf, (x,y))


__all__ = [
    'getFont',
    'drawText',
    'drawRect',
    'drawLine',
    'drawRectShaded',
    'drawTextShaded'
]



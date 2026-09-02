from types import ModuleType
from typing import Literal
import pygame.gfxdraw
import pygame
import json
import os

from ..constants import game, VERSION

### Shader Functions ###
# Cache for static shader surfaces
_static_shader_cache = {}

def load_as_module(source, name, globals=None) -> ModuleType:
    # sourcery skip: avoid-builtin-shadow
    if globals is None:
        globals = {}
    module = ModuleType(name)
    module.__dict__.update(globals)
    exec(source, module.__dict__)
    return module

def loadShaderMeta(shader_pack) -> tuple[Literal['Error'], str] | dict:
    metapath = os.path.join(shader_pack, 'shader.json')

    with open(metapath) as f:
        meta = json.load(f)

    require = meta['require']

    if game and game.id in require:
        ver = require[game.id]
        try: compatible = ver == '*' or eval(f'{game.VERSION}{ver}')
        except: compatible = False
        if not compatible:
            return 'Error', f'This shader requires platformer version {ver}.'

    if 'engine' in require:
        ver = require['engine']
        try: compatible = ver == '*' or eval(f'{VERSION}{ver}')
        except: compatible = False
        if not compatible:
            return 'Error', f'This shader requires engine version {ver}.'

    return meta

def loadShaderFile(shader_pack, shader_file, globals=None):
    # sourcery skip: avoid-builtin-shadow
    if globals is None:
        globals = {}
    meta = loadShaderMeta(shader_pack)
    if isinstance(meta, tuple) and meta[0] == 'Error':
        return meta  # propagate error

    shader_meta = next((s for s in meta['shaders'] if s['filename'] == shader_file), None)

    if not shader_meta:
        print(f'Error while loading shader {shader_file}: Could not find shader meta.')
        return

    if shader_meta.get('args'):
        if missing_args := [
            arg for arg in shader_meta['args'] if arg not in globals
        ]:
            return 'Error', f'Shader {shader_file} missing {len(missing_args)} arguments: {str(missing_args).strip("[]")}'

    with open(os.path.join(shader_pack, shader_file)) as f:
        try:
            module = load_as_module(f.read(), f.name, globals)
            shader_func = module.shader

            if shader_meta.get('cache', False):
                from ..modules.utils import cache
                shader_func = cache(ignore=shader_meta.get('ignore_args', []))(shader_func)

            # Build static cache key from args (excluding 'gl')
            static_cache_key = None
            if shader_meta.get('static', False):
                cache_args = {k: v for k, v in globals.items() if k != 'gl' and k in shader_meta.get('args', [])}
                # Convert to hashable tuple of sorted items, converting lists to tuples
                def make_hashable(obj):
                    if isinstance(obj, list):
                        return tuple(make_hashable(item) for item in obj)
                    elif isinstance(obj, dict):
                        return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
                    return obj
                static_cache_key = (shader_pack, shader_file, make_hashable(cache_args))

            # Attach metadata to the function
            shader_func._static = shader_meta.get('static', False)
            shader_func._static_cache_key = static_cache_key

            return shader_func

        except Exception as e:
            print(f'Error while loading shader {shader_file}: {e}')
            return

def loadShaders(shader_pack, shader_index=None):
    meta = loadShaderMeta(shader_pack)
    if not isinstance(meta, dict):
        return meta

    shaders = meta['shaders']

    if not shader_index:
        bg_shaders = []
        sprite_shaders = []

        for shader in shaders:
            if shader['type'] not in {'background','sprite'}:
                return 'Error', f'Unsupported shader type: {shader["type"]}'

            shader_func, cache = loadShaderFile(shader_pack, shader['filename'])

            if shader['type'] == 'background':
                bg_shaders.append((shader_func, cache))

            elif shader['type'] == 'sprite':
                sprite_shaders.append((shader_func, cache))

        return meta, bg_shaders, sprite_shaders

    shader = shaders[shader_index]

    if shader['type'] not in {'background','sprite'}:
        return 'Error', f'Unsupported shader type: {shader["type"]}'

    return loadShaderFile(shader_pack, shader['filename'])

def applyShader(surf, shader, res=4, mask=None, view_rect=None, args=None) -> pygame.Surface:
    """
        Applies a shader to a surface.

        Args:
            surf: The surface to apply the shader to.
            shader: A function that takes a color and returns a modified color.
            res: The resolution of the shader application (default is 4).
            mask: A color to not shade. (wont be visible)
            view_rect: Optional (x, y, width, height) to limit shader processing to visible area
    """
    if args is None:
        args = []

    # Check for static shader cache
    if hasattr(shader, '_static') and shader._static and shader._static_cache_key:
        cache_key = (shader._static_cache_key, surf.get_size(), res)
        if cache_key in _static_shader_cache:
            return _static_shader_cache[cache_key].copy()

    # Create a new surface with alpha support
    result_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)

    # Copy initial surface
    result_surf.blit(surf, (0, 0))

    # Determine bounds for processing
    if view_rect:
        # Only process the visible part of the surface
        min_x = max(0, view_rect[0])
        min_y = max(0, view_rect[1])
        max_x = min(surf.get_width(), view_rect[0] + view_rect[2])
        max_y = min(surf.get_height(), view_rect[1] + view_rect[3])
    else:
        # Process the entire surface if no view rect specified
        min_x, min_y = 0, 0
        max_x, max_y = surf.get_width(), surf.get_height()

    # Process only the pixels within bounds
    for y in range(min_y, max_y, res):
        for x in range(min_x, max_x, res):
            try:
                color = surf.get_at((x, y))

                # Always skip completely transparent pixels
                if color.a == 0:
                    continue

                # If using mask and this is a masked color, make it transparent
                if mask and color.r == mask[0] and color.g == mask[1] and color.b == mask[2]:
                    result_surf.set_at((x, y), (0, 0, 0, 0))
                    continue

                # Apply shader and update
                new_color = shader(color, x, y, game.frame, *args)

                if not new_color:
                    continue
                rect = (x, y, res, res)
                pygame.gfxdraw.box(result_surf, rect, new_color)

            except IndexError:
                continue  # Handle edge case errors

    # Cache static shader result
    if hasattr(shader, '_static') and shader._static and shader._static_cache_key:
        cache_key = (shader._static_cache_key, surf.get_size(), res)
        _static_shader_cache[cache_key] = result_surf.copy()

    return result_surf


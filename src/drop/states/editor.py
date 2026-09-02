from pathlib import Path
from tkinter import Tk, filedialog

import engine as gl

from .level_select import LEVELS_DIR, Level, load_level
from .play import Object


GRID_SIZES = (1, 2, 5, 10, 20)
GRID_COLOR = (35, 35, 35)
OBJECT_COLOR = (255, 255, 255)
SELECTED_COLOR = (80, 220, 120)
PLAY_START_FRAME = 10
TIME_SCALE = 7
PLAYER_MIDPOINT = 50
PLAYER_SIZE = 25
NORMAL_FRAME_RATE = 60


class EditorState:
    def __init__(self, game, level=None, exit_to_select=None):
        self.game = game
        self.level = level
        self.exit_to_select = exit_to_select
        self.objects = set() if level is None else level.objects.copy()
        self.level_name = 'New level' if level is None else level.name
        self.level_description = '' if level is None else level.description
        self.time_offset = 0
        self.grid_index = 2
        self.action = None
        self.action_start = None
        self.action_object = None
        self.action_original = None
        self.safe_create = False
        self.hovered_object = None
        self.dirty = False
        self.playing = False
        self.player_x = 50
        self.move_state = 0
        self.pressed_left = [False, False]
        self.pressed_right = [False, False]

    @property
    def grid_size(self):
        return GRID_SIZES[self.grid_index]

    def on_enter(self):
        pass

    def update(self, dt):
        if self.playing:
            self.time_offset += dt * NORMAL_FRAME_RATE
            self.player_x += self.move_state * dt * 50
            self.player_x = gl.clamp(self.player_x, min_=PLAYER_SIZE / 10, max_=100 - PLAYER_SIZE / 10)

    def on_frame(self, frame_num):
        self.draw_grid()
        zero_y = (PLAY_START_FRAME - self.time_offset) * 5
        gl.drawLine((0, zero_y), (500, zero_y), (180, 60, 60), 2)
        gl.drawLine((0, PLAYER_MIDPOINT), (500, PLAYER_MIDPOINT), (255, 30, 30), 2)
        gl.drawText('EDITOR', 20, 20, 28)
        gl.drawText(f'Grid: {self.grid_size:g}', 20, 55, 16)

        for obj in sorted(self.objects, key=lambda value: value.time):
            self.draw_object(obj, obj is self.hovered_object)

        if self.playing:
            gl.drawRect(
                (self.player_x * 5 - PLAYER_SIZE / 2, PLAYER_MIDPOINT - PLAYER_SIZE / 2, PLAYER_SIZE, PLAYER_SIZE),
                (255, 0, 0),
            )

        if self.action == 'create' and self.action_start:
            current = self.mouse_position
            previews = self.make_safe_objects(self.action_start, current) if self.safe_create else [self.make_object(self.action_start, current)]
            for preview in previews:
                if preview:
                    self.draw_object(preview, True)

    def draw_grid(self):
        for x in range(0, 101, self.grid_size):
            screen_x = x * 5
            gl.drawLine((screen_x, 0), (screen_x, 700), GRID_COLOR)

        first_time = int(self.time_offset // self.grid_size) * self.grid_size
        last_time = int(self.time_offset + 140) + self.grid_size

        for time in range(first_time, last_time, self.grid_size):
            screen_y = (time - self.time_offset) * 5
            gl.drawLine((0, screen_y), (500, screen_y), GRID_COLOR)

    def draw_object(self, obj, selected=False):
        x = obj.x * 5
        y = self.screen_y(obj)

        width = obj.width * 5
        height = obj.height * TIME_SCALE

        color = SELECTED_COLOR if selected else OBJECT_COLOR

        gl.drawRect((x, y, width, height), color)
        gl.drawRect((x, y, width, height), (0, 0, 0), 2)

        speed_width = gl.textSize(f'{obj.speed:.1f}', 16)[0]
        move_speed_width = gl.textSize(f'{obj.move_speed:.1f}', 16)[0]

        gl.drawText(f'{obj.speed:.1f}', x + (width - speed_width) / 2, y + 3, 16, (0, 0, 0))
        gl.drawText(f'{obj.move_speed:.1f}', x + (width - move_speed_width) / 2, y + 20, 16, (0, 0, 0))

    def on_mouse_move(self, event):
        self.mouse_position = event['pos']
        position = event['pos']
        if self.action == 'move' and self.action_object:
            self.move_object(position)
        elif self.action == 'resize' and self.action_object:
            self.resize_object(position)
        else:
            self.hovered_object = self.object_at(position)

    def on_mouse_down(self, event):
        if event['button'] == gl.pygame.BUTTON_LEFT:
            self.action = 'create'
            self.action_start = self.snap_position(event['pos'])
            self.mouse_position = event['pos']
            self.safe_create = bool(gl.pygame.key.get_mods() & gl.pygame.KMOD_ALT)
        elif event['button'] == gl.pygame.BUTTON_RIGHT:
            self.action_object = self.object_at(event['pos'])
            if self.action_object:
                self.action = 'move'
                self.action_start = event['pos']
                self.action_original = self.action_object
        elif event['button'] == gl.pygame.BUTTON_MIDDLE:
            self.action_object = self.object_at(event['pos'])
            if self.action_object:
                self.action = 'resize'
                self.action_start = event['pos']
                self.action_original = self.action_object

    def on_mouse_up(self, event):
        if event['button'] == gl.pygame.BUTTON_LEFT and self.action == 'create':
            created = self.make_safe_objects(self.action_start, event['pos']) if self.safe_create else [self.make_object(self.action_start, event['pos'])]
            if any(created):
                self.objects.update(obj for obj in created if obj)
                self.dirty = True

        self.action = None
        self.action_start = None
        self.action_object = None
        self.action_original = None
        self.safe_create = False

    def on_scroll(self, event):
        hovered = self.object_at(getattr(event, 'pos', None)) if 'pos' in event else self.hovered_object
        modifiers = gl.pygame.key.get_mods()
        if modifiers & gl.pygame.KMOD_ALT:
            direction = 1 if event['y'] > 0 else -1
            self.grid_index = max(0, min(len(GRID_SIZES) - 1, self.grid_index + direction))

        elif hovered and modifiers & gl.pygame.KMOD_CTRL:
            speed = max(0.1, hovered.speed + event['y'] * 0.1)
            self.replace_object(hovered, speed=speed)

        elif hovered and modifiers & gl.pygame.KMOD_SHIFT:
            self.replace_object(hovered, move_speed=max(0, hovered.move_speed + event['y'] * 0.1))

        else:
            self.time_offset -= event['y'] * self.grid_size

    def on_key_down(self, key):
        modifiers = gl.pygame.key.get_mods()
        if key == gl.pygame.K_SPACE:
            self.playing = not self.playing
        elif key in (gl.pygame.K_LEFT, gl.pygame.K_a):
            self.pressed_left[key == gl.pygame.K_a] = True
            self.move_state = -1
        elif key in (gl.pygame.K_RIGHT, gl.pygame.K_d):
            self.pressed_right[key == gl.pygame.K_d] = True
            self.move_state = 1
        elif key == gl.pygame.K_DELETE and modifiers & gl.pygame.KMOD_CTRL and modifiers & gl.pygame.KMOD_SHIFT and modifiers & gl.pygame.KMOD_ALT:
            self.objects.clear()
            self.hovered_object = None
            self.dirty = True
            self.toast('Cleared all objects.')

        elif key == gl.pygame.K_DELETE and self.hovered_object:
            self.objects.discard(self.hovered_object)
            self.hovered_object = None
            self.dirty = True
            self.toast('Object deleted.')

        elif key == gl.pygame.K_ESCAPE and self.exit_to_select:
            self.exit_to_select()

        elif key in (gl.pygame.K_EQUALS, gl.pygame.K_PLUS) and not modifiers & gl.pygame.KMOD_CTRL:
            self.grid_index = min(len(GRID_SIZES) - 1, self.grid_index + 1)
            self.toast(f'Grid size: {self.grid_index}')

        elif key == gl.pygame.K_MINUS and not modifiers & gl.pygame.KMOD_CTRL:
            self.grid_index = max(0, self.grid_index - 1)
            self.toast(f'Grid size: {self.grid_index}')

        elif key == gl.pygame.K_s and modifiers & gl.pygame.KMOD_CTRL:
            self.save()

    def on_key_up(self, key):
        if key in (gl.pygame.K_LEFT, gl.pygame.K_a):
            self.pressed_left[key == gl.pygame.K_a] = False
            if not any(self.pressed_left):
                self.move_state = 1 if any(self.pressed_right) else 0
        elif key in (gl.pygame.K_RIGHT, gl.pygame.K_d):
            self.pressed_right[key == gl.pygame.K_d] = False
            if not any(self.pressed_right):
                self.move_state = -1 if any(self.pressed_left) else 0

    def snap_position(self, position):
        x, y = position
        return (
            round(x / 5 / self.grid_size) * self.grid_size,
            round(self.time_from_y(y) / self.grid_size) * self.grid_size,
        )

    def make_object(self, start, end):
        start_x, start_time = start
        end_x, end_time = self.snap_position(end)
        x = min(start_x, end_x)
        time = min(start_time, end_time)
        width = max(self.grid_size, abs(end_x - start_x))
        height = max(self.grid_size, abs(end_time - start_time))
        x = min(100 - width, max(0, x))
        time = self.clamp_time(time, height)
        return Object(time, x, width, height)

    def object_at(self, position):
        if position is None:
            return None
        x, y = position
        return next(
            (
                candidate for candidate in reversed(sorted(self.objects, key=lambda value: value.time))
                if candidate.x * 5 <= x <= (candidate.x + candidate.width) * 5
                and self.screen_y(candidate) <= y <= self.screen_y(candidate) + candidate.height * TIME_SCALE
            ),
            None,
        )

    def move_object(self, position):
        obj = self.action_object
        original = self.action_original
        start_x, start_time = self.world_position(self.action_start, original.speed)
        current_x, current_time = self.world_position(position, original.speed)
        delta_x = round((current_x - start_x) / self.grid_size) * self.grid_size
        delta_time = round((current_time - start_time) / self.grid_size) * self.grid_size
        x = min(100 - original.width, max(0, original.x + delta_x))
        time = self.clamp_time(original.time + delta_time, original.height, original.speed)
        self.replace_object(obj, x=x, time=time)

    def resize_object(self, position):
        obj = self.action_object
        original = self.action_original
        start_x, start_time = self.world_position(self.action_start, original.speed)
        x, time = self.world_position(position, original.speed)
        delta_x = round((x - start_x) / self.grid_size) * self.grid_size
        delta_time = round((time - start_time) / self.grid_size) * self.grid_size
        width = max(self.grid_size, original.width + delta_x)
        height = max(self.grid_size, original.height + delta_time)
        width = min(width, 100 - original.x)
        max_height = self.time_from_y(700, original.speed) - original.time
        height = min(height, max(self.grid_size, max_height))
        self.replace_object(obj, width=width, height=height)

    def clamp_time(self, time, height, speed=1):
        max_time = self.time_from_y(700 - height * TIME_SCALE, speed)
        return max(0, min(max_time, time))

    def world_position(self, position, speed=1):
        x, y = position
        return x / 5, self.time_from_y(y, speed)

    def screen_y(self, obj):
        base_y = obj.time * TIME_SCALE - (self.time_offset - PLAY_START_FRAME) * 5
        return PLAYER_MIDPOINT + (base_y - PLAYER_MIDPOINT) * obj.speed

    def time_from_y(self, y, speed=1):
        base_y = PLAYER_MIDPOINT + (y - PLAYER_MIDPOINT) / speed
        return (base_y + (self.time_offset - PLAY_START_FRAME) * 5) / TIME_SCALE

    def replace_object(self, old, **changes):
        new = Object(
            changes.get('time', old.time),
            changes.get('x', old.x),
            changes.get('width', old.width),
            changes.get('height', old.height),
            changes.get('speed', old.speed),
            changes.get('move_speed', old.move_speed),
        )
        self.objects.remove(old)
        self.objects.add(new)
        self.action_object = new
        self.hovered_object = new
        self.dirty = True

    def save(self):
        if self.level and self.level.path:
            path = self.level.path
        else:
            root = Tk()
            root.withdraw()
            file_name = filedialog.asksaveasfilename(
                initialdir=str(LEVELS_DIR),
                initialfile='level.lvl',
                defaultextension='.lvl',
                filetypes=(('Drop levels', '*.lvl'), ('All files', '*.*')),
            )
            root.destroy()
            if not file_name:
                return

            path = Path(file_name)

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as level_file:
            level_file.write(f':name {self.level_name}\n')
            level_file.write(f':description {self.level_description}\n\n')
            for obj in sorted(self.objects, key=lambda value: value.time):
                level_file.write(','.join(f'{value:.3f}' for value in obj) + '\n')

        self.level = Level(self.objects.copy(), self.level_name, self.level_description, path)
        self.dirty = False

        self.toast('Saved.')

    def make_safe_objects(self, start, end):
        safe_space = self.make_object(start, end)
        left_width = safe_space.x
        right_x = safe_space.x + safe_space.width
        right_width = 100 - right_x
        objects = []
        if left_width > 0:
            objects.append(Object(safe_space.time, 0, left_width, safe_space.height))
        if right_width > 0:
            objects.append(Object(safe_space.time, right_x, right_width, safe_space.height))
        return objects

    def toast(self, text):
        gl.Toast(
            (self.game.width * self.game.res - 5, self.game.height * self.game.res - 5),
            text,
            20,
            duration=2000
        )

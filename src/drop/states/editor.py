from tkinter import filedialog, Tk
from pathlib import Path

from .level_select import load_level, LEVELS_DIR, Level
from .play import Object
import engine as gl


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
        self.selected_objects = set()
        self.selection_start = None
        self.selection_add = False
        self.action_objects = set()
        self.action_originals = {}
        self.action_current = set()
        self.action_before = None
        self.action_preserve_selection = False
        self.history = [self.snapshot()]
        self.history_index = 0

    @property
    def grid_size(self):
        return GRID_SIZES[self.grid_index]

    def on_enter(self):
        self.update_title()

    def update(self, dt):
        if self.playing:
            self.time_offset += dt * NORMAL_FRAME_RATE
            self.player_x += self.move_state * dt * 50
            self.player_x = gl.clamp(self.player_x, min_=PLAYER_SIZE / 10, max_=100 - PLAYER_SIZE / 10)

    def update_title(self):
        file_name = self.level.path.name if self.level and self.level.path else 'untitled.txt'
        suffix = '*' if self.dirty else ''
        self.game.title = f'Drop 1a | Editor - {file_name}{suffix}'

    def on_frame(self, frame_num):
        self.update_title()
        self.draw_grid()

        zero_y = (PLAY_START_FRAME - self.time_offset) * 5
        gl.drawLine((0, zero_y), (500, zero_y), (180, 60, 60), 2)
        gl.drawLine((0, PLAYER_MIDPOINT), (500, PLAYER_MIDPOINT), (255, 30, 30), 2)
        gl.drawText('EDITOR', 20, 20, 28)
        gl.drawText(f'Grid: {self.grid_size:g}', 20, 55, 16)

        for obj in sorted(self.objects, key=lambda value: value.time):
            self.draw_object(obj, obj in self.selected_objects or obj is self.hovered_object)

        self.draw_selection()

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
        if self.action == 'select':
            return

        elif self.action == 'move' and self.action_object:
            self.move_object(position)

        elif self.action == 'resize' and self.action_object:
            self.resize_object(position)

        else:
            self.hovered_object = self.object_at(position)

    def on_mouse_down(self, event):
        if event['button'] == gl.pygame.BUTTON_LEFT:
            modifiers = gl.pygame.key.get_mods()
            clicked = self.object_at(event['pos'])

            self.selection_add = bool(
                modifiers & (gl.pygame.KMOD_SHIFT | gl.pygame.KMOD_CTRL)
            )

            if clicked:
                self.select_object(clicked, self.selection_add)
                self.action = 'select'
                self.selection_start = event['pos']
                self.mouse_position = event['pos']

            elif self.selection_add:
                self.action = 'select'
                self.selection_start = event['pos']
                self.mouse_position = event['pos']

            else:
                self.selected_objects.clear()
                self.action = 'create'
                self.action_start = self.snap_position(event['pos'])
                self.mouse_position = event['pos']
                self.safe_create = bool(modifiers & gl.pygame.KMOD_ALT)

        elif event['button'] == gl.pygame.BUTTON_RIGHT:
            self.action_object = self.object_at(event['pos'])
            if self.action_object:
                self.action = 'move'
                self.action_start = event['pos']
                self.action_original = self.action_object
                self.action_preserve_selection = self.action_object in self.selected_objects
                self.action_objects = self.selected_objects if self.action_preserve_selection else {self.action_object}
                self.action_originals = {obj: obj for obj in self.action_objects}
                self.action_current = set(self.action_objects)
                self.action_before = self.snapshot()

        elif event['button'] == gl.pygame.BUTTON_MIDDLE:
            self.action_object = self.object_at(event['pos'])
            if self.action_object:
                self.action = 'resize'
                self.action_start = event['pos']
                self.action_original = self.action_object
                self.action_preserve_selection = self.action_object in self.selected_objects
                self.action_objects = self.selected_objects if self.action_preserve_selection else {self.action_object}
                self.action_originals = {obj: obj for obj in self.action_objects}
                self.action_current = set(self.action_objects)
                self.action_before = self.snapshot()

    def on_mouse_up(self, event):
        if event['button'] == gl.pygame.BUTTON_LEFT and self.action == 'select':
            self.select_in_rectangle(self.selection_start, event['pos'], self.selection_add)
            self.selection_start = None
            self.action = None
            return

        if event['button'] == gl.pygame.BUTTON_LEFT and self.action == 'create':
            created = self.make_safe_objects(self.action_start, event['pos']) if self.safe_create else [self.make_object(self.action_start, event['pos'])]
            if any(created):
                self.objects.update(obj for obj in created if obj)
                self.dirty = True
                self.commit_history()

        if self.action in ('move', 'resize'):
            self.commit_history()

        self.action = None
        self.action_start = None
        self.action_object = None
        self.action_original = None
        self.action_objects = set()
        self.action_originals = {}
        self.action_current = set()
        self.action_before = None
        self.action_preserve_selection = False
        self.safe_create = False

    def on_scroll(self, event):
        hovered = self.object_at(getattr(event, 'pos', None)) if 'pos' in event else self.hovered_object
        modifiers = gl.pygame.key.get_mods()
        if modifiers & gl.pygame.KMOD_ALT:
            direction = 1 if event['y'] > 0 else -1
            self.grid_index = max(0, min(len(GRID_SIZES) - 1, self.grid_index + direction))

        elif hovered and modifiers & gl.pygame.KMOD_CTRL:
            self.change_selected_property('speed', event['y'] * 0.1)

        elif hovered and modifiers & gl.pygame.KMOD_SHIFT:
            self.change_selected_property('move_speed', event['y'] * 0.1)

        else:
            self.time_offset -= event['y'] * self.grid_size

    def on_key_down(self, key):
        modifiers = gl.pygame.key.get_mods()
        if key == gl.pygame.K_SPACE:
            self.playing = not self.playing

        elif key == gl.pygame.K_z and modifiers & gl.pygame.KMOD_CTRL and modifiers & gl.pygame.KMOD_SHIFT:
            self.redo()

        elif key == gl.pygame.K_z and modifiers & gl.pygame.KMOD_CTRL:
            self.undo()

        elif key == gl.pygame.K_d and modifiers & gl.pygame.KMOD_CTRL:
            self.selected_objects.clear()

        elif key in (gl.pygame.K_LEFT, gl.pygame.K_a):
            self.pressed_left[key == gl.pygame.K_a] = True
            self.move_state = -1

        elif key in (gl.pygame.K_RIGHT, gl.pygame.K_d):
            self.pressed_right[key == gl.pygame.K_d] = True
            self.move_state = 1

        elif key == gl.pygame.K_DELETE and modifiers & gl.pygame.KMOD_CTRL and modifiers & gl.pygame.KMOD_SHIFT and modifiers & gl.pygame.KMOD_ALT:
            self.objects.clear()
            self.selected_objects.clear()
            self.hovered_object = None
            self.dirty = True
            self.commit_history()
            self.toast('Cleared all objects.')

        elif key == gl.pygame.K_DELETE and (self.selected_objects or self.hovered_object):
            targets = self.selected_objects or {self.hovered_object}
            self.objects.difference_update(targets)
            self.selected_objects.difference_update(targets)
            self.hovered_object = None
            self.dirty = True
            self.commit_history()
            self.toast('Object deleted.')

        elif key == gl.pygame.K_ESCAPE and self.exit_to_select:
            if self.dirty:
                self.confirm_leave = True
                self.playing = False
            else:
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

    def select_object(self, obj, add):
        if not add:
            self.selected_objects.clear()

        self.selected_objects.add(obj)

    def select_in_rectangle(self, start, end, add):
        left = min(start[0], end[0])
        top = min(start[1], end[1])
        right = max(start[0], end[0])
        bottom = max(start[1], end[1])
        selected = {
            obj for obj in self.objects
            if self.rectangles_intersect(
                (left, top, right, bottom),
                self.object_rect(obj),
            )
        }
        if not add:
            self.selected_objects.clear()

        self.selected_objects.update(selected)

    def object_rect(self, obj):
        x = obj.x * 5
        y = self.screen_y(obj)
        return x, y, x + obj.width * 5, y + obj.height * TIME_SCALE

    def rectangles_intersect(self, first, second):
        return (
            first[0] <= second[2]
            and first[2] >= second[0]
            and first[1] <= second[3]
            and first[3] >= second[1]
        )

    def draw_selection(self):
        if self.action != 'select' or not self.selection_start:
            return

        end = self.mouse_position
        left = min(self.selection_start[0], end[0])
        top = min(self.selection_start[1], end[1])
        width = abs(end[0] - self.selection_start[0])
        height = abs(end[1] - self.selection_start[1])
        surface = gl.pygame.Surface((width + 1, height + 1), gl.pygame.SRCALPHA)
        surface.fill((80, 180, 255, 70))
        gl.pygame.draw.rect(surface, (140, 220, 255, 190), surface.get_rect(), 1)
        self.game.disp.blit(surface, (left, top))

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
        anchor = self.action_original
        start_x, start_time = self.world_position(self.action_start, anchor.speed)
        current_x, current_time = self.world_position(position, anchor.speed)
        delta_x = round((current_x - start_x) / self.grid_size) * self.grid_size
        delta_time = round((current_time - start_time) / self.grid_size) * self.grid_size
        replacements = {
            original: Object(
                self.clamp_time(original.time + delta_time, original.height, original.speed),
                min(100 - original.width, max(0, original.x + delta_x)),
                original.width,
                original.height,
                original.speed,
                original.move_speed,
            )
            for original in self.action_originals.values()
        }
        self.replace_group(replacements)

    def resize_object(self, position):
        anchor = self.action_original
        start_x, start_time = self.world_position(self.action_start, anchor.speed)
        x, time = self.world_position(position, anchor.speed)
        delta_x = round((x - start_x) / self.grid_size) * self.grid_size
        delta_time = round((time - start_time) / self.grid_size) * self.grid_size
        replacements = {}
        for original in self.action_originals.values():
            width = min(max(self.grid_size, original.width + delta_x), 100 - original.x)
            height = max(self.grid_size, original.height + delta_time)
            max_height = self.time_from_y(700, original.speed) - original.time
            height = min(height, max(self.grid_size, max_height))
            replacements[original] = Object(
                original.time,
                original.x,
                width,
                height,
                original.speed,
                original.move_speed,
            )
        self.replace_group(replacements)

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

    def replace_group(self, replacements):
        self.objects.difference_update(self.action_current)
        self.objects.update(replacements.values())
        self.action_current = set(replacements.values())
        if self.action_preserve_selection:
            self.selected_objects = set(replacements.values())

        self.action_object = next(iter(self.action_current), None)
        self.hovered_object = self.action_object
        self.dirty = True

    def change_selected_property(self, property_name, delta):
        targets = self.selected_objects or ({self.hovered_object} if self.hovered_object else set())
        preserve_selection = bool(self.selected_objects)
        old_hovered = self.hovered_object
        replacements = {}
        for old in targets:
            values = {
                'time': old.time,
                'x': old.x,
                'width': old.width,
                'height': old.height,
                'speed': old.speed,
                'move_speed': old.move_speed,
            }
            values[property_name] = max(0.1, values[property_name] + delta) if property_name == 'speed' else values[property_name] + delta
            replacements[old] = Object(**values)

        if replacements:
            self.objects.difference_update(replacements)
            self.objects.update(replacements.values())
            if preserve_selection:
                self.selected_objects = set(replacements.values())

            self.hovered_object = replacements.get(old_hovered, old_hovered)
            self.dirty = True
            self.commit_history()

    def snapshot(self):
        return frozenset(self.objects), frozenset(self.selected_objects)

    def commit_history(self):
        state = self.snapshot()
        if state == self.history[self.history_index]:
            return

        self.history = self.history[:self.history_index + 1]
        self.history.append(state)
        self.history = self.history[-50:]
        self.history_index = len(self.history) - 1

    def restore_history(self, state):
        self.objects = set(state[0])
        self.selected_objects = set(state[1])
        self.hovered_object = None
        self.dirty = True

    def undo(self):
        if self.history_index == 0:
            return

        self.history_index -= 1
        self.restore_history(self.history[self.history_index])

    def redo(self):
        if self.history_index >= len(self.history) - 1:
            return

        self.history_index += 1
        self.restore_history(self.history[self.history_index])

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
                values = self.serialized_object(obj)
                level_file.write(
                    ','.join(
                        f'{value:.3f}'.rstrip('0').removesuffix('.')
                        for value in values
                    ) + '\n'
                )

        self.level = Level(self.objects.copy(), self.level_name, self.level_description, path)
        self.dirty = False

        self.toast('Saved.')

    def serialized_object(self, obj):
        values = [obj.time, obj.x, obj.width, obj.height, obj.speed, obj.move_speed]
        defaults = (1.0, 1.0, 1.0, 0.0)
        while len(values) > 2 and values[-1] == defaults[len(values) - 3]:
            values.pop()
        return values

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

from dataclasses import dataclass
import json
from pathlib import Path

from .play import Object, USER_FILE
import engine as gl


LEVELS_DIR = Path(__file__).parent.parent / 'levels'
LIST_TOP = 190
LIST_BOTTOM = 650
ROW_HEIGHT = 35
QUIT_RECT = (400, 105, 70, 40)
EDITOR_RECT = (280, 105, 105, 40)


@dataclass
class Level:
    objects: set[Object]
    name: str = 'Unnamed level'
    description: str = ''
    path: Path | None = None

    @property
    def length(self):
        return max((object.time for object in self.objects), default=0)

def float_all(*args):
    return map(float, args)

def load_level(file: str | Path) -> Level:
    objects = set()
    metadata = {}

    with open(file) as level_file:
        for line in level_file:
            line = line.strip()
            if not line:
                continue

            if line.startswith(':'):
                property_name, _, value = line[1:].partition(' ')
                metadata[property_name] = value.strip()
                continue

            objects.add(Object(*float_all(*line.split(','))))

    return Level(
        objects,
        metadata.get('name', 'Unnamed level'),
        metadata.get('description', ''),
        Path(file),
    )


class LevelSelectState:
    def __init__(self, game, start_play, open_editor, quit_game, levels_dir=LEVELS_DIR):
        self.game = game
        self.start_play = start_play
        self.open_editor = open_editor
        self.quit_game = quit_game
        self.levels_dir = Path(levels_dir)
        self.levels = []
        self.selected = 0
        self.scroll = 0
        self.selected_level = None
        self.cleared_levels = set()

    def on_enter(self):
        levels = []
        levels.extend(
            (path, load_level(path))
            for path in self.levels_dir.iterdir()
            if path.is_file()
        )
        self.levels = sorted(
            levels,
            key=lambda item: (item[1].length, len(item[0].name), item[0].name.lower()),
        )
        if USER_FILE.exists():
            with open(USER_FILE) as user_file:
                self.cleared_levels = set(json.load(user_file).get('cleared_levels', []))
        self.selected = min(self.selected, max(0, len(self.levels) - 1))
        self.scroll = 0
        if self.levels:
            self.selected_level = self.levels[self.selected][1]

    def update(self, dt):
        pass

    def on_frame(self, frame_num):
        gl.drawText('SELECT A LEVEL', 70, 113, 23)
        gl.drawText('Editor', 290, 115, 20)
        gl.drawText('Quit', 410, 115, 20)

        if not self.levels:
            gl.drawText('No levels found', 75, LIST_TOP, 20)
            return

        visible_rows = (LIST_BOTTOM - LIST_TOP) // ROW_HEIGHT
        for index in range(self.scroll, min(len(self.levels), self.scroll + visible_rows)):
            path, level = self.levels[index]
            color = (255, 255, 0) if index == self.selected else (255, 255, 255)
            if path.name in self.cleared_levels:
                color = (80, 220, 220)
            if index == self.selected:
                color = (80, 220, 220) if path.name in self.cleared_levels else (255, 255, 0)
            gl.drawText(level.name, 75, LIST_TOP + (index - self.scroll) * ROW_HEIGHT, 24, color)

        if self.selected_level.description:
            gl.drawText(self.selected_level.description, 75, LIST_BOTTOM + 10, 16)

    def on_key_down(self, key):
        if not self.levels:
            return
        if key in (gl.pygame.K_UP, gl.pygame.K_w):
            self.select(self.selected - 1)
        elif key in (gl.pygame.K_DOWN, gl.pygame.K_s):
            self.select(self.selected + 1)
        elif key == gl.pygame.K_RETURN:
            self.start_play(self.selected_level)

    def on_mouse_move(self, event):
        self.select_at(event['pos'])

    def on_mouse_down(self, event):
        if event['button'] != gl.pygame.BUTTON_LEFT:
            return
        x, y = event['pos']
        if QUIT_RECT[0] <= x <= QUIT_RECT[0] + QUIT_RECT[2] and QUIT_RECT[1] <= y <= QUIT_RECT[1] + QUIT_RECT[3]:
            self.quit_game()
        elif EDITOR_RECT[0] <= x <= EDITOR_RECT[0] + EDITOR_RECT[2] and EDITOR_RECT[1] <= y <= EDITOR_RECT[1] + EDITOR_RECT[3]:
            self.open_editor()
        elif self.select_at(event['pos']):
            self.start_play(self.selected_level)

    def on_mouse_up(self, event):
        if event['button'] == gl.pygame.BUTTON_RIGHT:
            if level := self.object_level_at(event['pos']):
                self.open_editor(level)

    def object_level_at(self, position):
        x, y = position
        visible_rows = (LIST_BOTTOM - LIST_TOP) // ROW_HEIGHT
        if not (75 <= x <= 450 and LIST_TOP <= y < LIST_TOP + visible_rows * ROW_HEIGHT):
            return None
        index = self.scroll + (y - LIST_TOP) // ROW_HEIGHT
        return None if index >= len(self.levels) else self.levels[index][1]

    def on_scroll(self, event):
        visible_rows = (LIST_BOTTOM - LIST_TOP) // ROW_HEIGHT
        max_scroll = max(0, len(self.levels) - visible_rows)
        self.scroll = max(0, min(max_scroll, self.scroll - event['y']))

        if self.selected < self.scroll:
            self.select(self.scroll)
        elif self.selected >= self.scroll + visible_rows:
            self.select(self.scroll + visible_rows - 1)

    def select_at(self, position):
        x, y = position
        visible_rows = (LIST_BOTTOM - LIST_TOP) // ROW_HEIGHT
        if not (100 <= x <= 450 and LIST_TOP <= y < LIST_TOP + visible_rows * ROW_HEIGHT):
            return False

        index = self.scroll + (y - LIST_TOP) // ROW_HEIGHT
        if index >= len(self.levels):
            return False
        self.select(index)
        return True

    def select(self, index):
        self.selected = max(0, min(len(self.levels) - 1, index))
        self.selected_level = self.levels[self.selected][1]

        visible_rows = (LIST_BOTTOM - LIST_TOP) // ROW_HEIGHT
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + visible_rows:
            self.scroll = self.selected - visible_rows + 1

    def on_key_up(self, key):
        pass

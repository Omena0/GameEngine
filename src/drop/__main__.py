import engine as gl
from pathlib import Path
from .states.editor import EditorState
from .states.level_select import LevelSelectState, load_level
from .states.play import PlayState


game = gl.Game('Drop', (500, 700), res=10, max_fps=60, vsync=False)
current_state = None


def set_state(state):
    global current_state
    current_state = state
    current_state.on_enter()


def start_play(level):
    level_source = load_level(level.path) if getattr(level, 'path', None) else level
    set_state(PlayState(game, level_source, lambda: start_play(level_source), show_levels))


def quit_game():
    game.running = False


def show_levels():
    set_state(LevelSelectState(game, start_play, open_editor, quit_game))


def open_editor(level=None):
    set_state(EditorState(game, level, show_levels))


set_state(LevelSelectState(game, start_play, open_editor, quit_game))


@game.on('frame')
def frame(frame_num):
    current_state.update(game.dt)
    current_state.on_frame(frame_num)


@game.on('keyDown')
def keydown(key):
    current_state.on_key_down(key['key'])


@game.on('keyUp')
def keyup(key):
    current_state.on_key_up(key['key'])


@game.on('mouseMove')
def mouse_move(event):
    getattr(current_state, 'on_mouse_move', lambda event: None)(event)


@game.on('mouseDown')
def mouse_down(event):
    getattr(current_state, 'on_mouse_down', lambda event: None)(event)


@game.on('mouseUp')
def mouse_up(event):
    getattr(current_state, 'on_mouse_up', lambda event: None)(event)


@game.on('scroll')
def scroll(event):
    getattr(current_state, 'on_scroll', lambda event: None)(event)


game.run()

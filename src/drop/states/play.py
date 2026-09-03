from dataclasses import dataclass
from pathlib import Path
import json
from typing import Generator

import engine as gl


SCROLL_SPEED = 5
SPEED_APPLY_POINT = 600
PLAYER_SIZE = 25
USER_FILE = Path(__file__).parent.parent / 'user.json'
PASS_EXIT_RECT = (150, 350, 200, 60)


@dataclass(frozen=True)
class Object:
    time: float
    x: float
    width: float
    height: float
    speed: float = 1.0
    move_speed: float = 1.0

    def __iter__(self) -> Generator[float, None, None]:
        yield float(self.time)
        yield float(self.x)
        yield float(self.width)
        yield float(self.height)
        yield float(self.speed)
        yield float(self.move_speed)

class PlayState:
    def __init__(self, game, level: str | Path, retry, exit_to_select):
        self.game = game
        self.level = level
        self.retry = retry
        self.exit_to_select = exit_to_select
        self.objects: set[Object] = set()
        self.player_x = 50
        self.move_speed = 1
        self.move_state = 0
        self.pressed_left = [False, False]
        self.pressed_right = [False, False]
        self.game_over = 0
        self.paused = False
        self.hovered_button = None
        self.start_frame = 0
        self.level_passed = False
        self.pass_hovered = False

    def on_enter(self):
        self.objects = self.level.objects.copy()
        self.start_frame = self.game.frame

    def update(self, dt):
        if self.game_over or self.paused:
            return

        self.player_x += self.move_state * self.move_speed * dt * 50
        self.player_x = gl.clamp(self.player_x, min_=PLAYER_SIZE / 10, max_=100 - PLAYER_SIZE / 10)

    def collision_check(self, x, y, width, height) -> bool:
        player_left = self.player_x * 5 - PLAYER_SIZE / 2
        player_right = player_left + PLAYER_SIZE

        return (
            x + width > player_left
            and x < player_right
            and y + height > 50 - PLAYER_SIZE / 2
            and y < 50 + PLAYER_SIZE / 2
        )

    def on_frame(self, frame_num):
        frame_num -= self.start_frame
        if self.game_over:
            frame_num = self.game_over
        else:
            frame_num -= 500 / SCROLL_SPEED

        for obj in self.objects.copy():
            time, x, width, height, speed, mv_speed = obj
            x *= 5
            base_y = (time * 7) - (frame_num * SCROLL_SPEED)
            y = 50 + (base_y - 50) * speed
            width *= 5
            height *= 7
            if y + height < 0:
                self.objects.discard(obj)
            if y > 700:
                continue
            color = (255, 255, 255)
            if abs(y + height - SPEED_APPLY_POINT) < 10:
                color = (0, 255, 0)
                self.move_speed = mv_speed
            if self.collision_check(x, y, width, height):
                self.game_over = frame_num
                color = (255, 100, 100)
            gl.drawRect((x, y, width, height), color)

        if not self.objects and not self.game_over and not self.level_passed:
            self.level_passed = True
            self.mark_level_cleared()

        gl.drawLine((0, 50), (500, 50), (30, 30, 30), 2)
        gl.drawLine((0, SPEED_APPLY_POINT), (500, SPEED_APPLY_POINT), (100, 30, 30), 2)
        gl.drawRect(
            (self.player_x * 5 - PLAYER_SIZE / 2, 50 - PLAYER_SIZE / 2, PLAYER_SIZE, PLAYER_SIZE),
            (255, 0, 0),
        )

        if self.game_over:
            gl.drawText('Game Over', 126, 250, 40)

        if self.paused:
            self.draw_pause_menu()

        if self.level_passed:
            text = 'Level passed'
            text_width = gl.textSize(text, 40)[0]
            gl.drawText(text, (500 - text_width) / 2, 250, 40, (80, 220, 220))
            color = (80, 100, 140) if self.pass_hovered else (50, 60, 80)
            gl.drawRect(PASS_EXIT_RECT, color)
            gl.drawRect(PASS_EXIT_RECT, (220, 220, 220), 2)
            gl.drawText('Exit', 220, 368, 24)

    def mark_level_cleared(self):
        cleared = set()
        if USER_FILE.exists():
            with open(USER_FILE) as user_file:
                cleared.update(json.load(user_file).get('cleared_levels', []))
        cleared.add(self.level.path.name)
        with open(USER_FILE, 'w') as user_file:
            json.dump({'cleared_levels': sorted(cleared)}, user_file, indent=2)

    def draw_pause_menu(self):
        gl.drawRect((75, 120, 350, 460), (20, 20, 25))
        gl.drawRect((75, 120, 350, 460), (180, 180, 180), 3)
        gl.drawText('Paused', 175, 165, 40)

        self.draw_button('Continue', (125, 250, 250, 60), 'continue')
        self.draw_button('Retry', (125, 330, 250, 60), 'retry')
        self.draw_button('Exit', (125, 410, 250, 60), 'exit')

    def draw_button(self, text, rect, button):
        color = (80, 100, 140) if self.hovered_button == button else (50, 60, 80)
        gl.drawRect(rect, color)
        gl.drawRect(rect, (220, 220, 220), 2)
        gl.drawText(text, rect[0] + 85, rect[1] + 18, 24)

    def on_key_down(self, key):
        if key == gl.pygame.K_ESCAPE:
            self.paused = not self.paused
            return

        if self.paused:
            return

        if key in (gl.pygame.K_LEFT, gl.pygame.K_a):
            self.pressed_left[key == gl.pygame.K_a] = True
            self.move_state = -1

        elif key in (gl.pygame.K_RIGHT, gl.pygame.K_d):
            self.pressed_right[key == gl.pygame.K_d] = True
            self.move_state = 1

    def on_key_up(self, key):
        if key in (gl.pygame.K_LEFT, gl.pygame.K_a):
            self.pressed_left[key == gl.pygame.K_a] = False
            if not any(self.pressed_left):
                self.move_state = 1 if any(self.pressed_right) else 0

        elif key in (gl.pygame.K_RIGHT, gl.pygame.K_d):
            self.pressed_right[key == gl.pygame.K_d] = False
            if not any(self.pressed_right):
                self.move_state = -1 if any(self.pressed_left) else 0

    def on_mouse_move(self, event):
        if self.level_passed:
            x, y = event['pos']
            self.pass_hovered = self.button_contains(PASS_EXIT_RECT, x, y)
            return
        if not self.paused:
            return

        self.hovered_button = self.button_at(event['pos'])

    def on_mouse_down(self, event):
        if self.level_passed:
            if event['button'] == gl.pygame.BUTTON_LEFT:
                x, y = event['pos']
                if self.button_contains(PASS_EXIT_RECT, x, y):
                    self.exit_to_select()
            return
        if not self.paused or event['button'] != gl.pygame.BUTTON_LEFT:
            return

        button = self.button_at(event['pos'])
        if button == 'continue':
            self.paused = False
        elif button == 'retry':
            self.retry()
        elif button == 'exit':
            self.exit_to_select()

    def button_at(self, position):
        x, y = position
        buttons = (
            ('continue', (125, 250, 250, 60)),
            ('retry', (125, 330, 250, 60)),
            ('exit', (125, 410, 250, 60)),
        )

        return next(
            (
                button for button, rect in buttons
                if rect[0] <= x <= rect[0] + rect[2]
                and rect[1] <= y <= rect[1] + rect[3]
            ),
            None,
        )

    def button_contains(self, rect, x, y):
        return rect[0] <= x <= rect[0] + rect[2] and rect[1] <= y <= rect[1] + rect[3]

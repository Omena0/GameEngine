from collections import defaultdict
try:
    import engine as gl
except ImportError:
    gl = None

PLAYER_SIZE = 25
PLAY_START_FRAME = 50
TIMELINE_BAR_BOTTOM = 16

def compute_reachability(objects, tolerance):
    """
    Compute reachable x-positions for each editor time row.
    Simulates forward from player start in EDITOR TIME.
    Player starts at t=PLAY_START_FRAME (10), x=50.
    Objects block across their full time range [t_obj, t_obj + height].
    Returns (reachable_grid, max_time) where reachable_grid[t][x] is True if reachable.
    """
    PLAYER_RADIUS = PLAYER_SIZE / 2.1
    TIME_SCALE = 7
    SCROLL_SPEED = 5

    tol_px = tolerance
    eff_radius_px = PLAYER_RADIUS + tol_px
    eff_radius = eff_radius_px / 5.0

    BASE_DX_PER_EDITOR_TIME = 50.0 * TIME_SCALE / (SCROLL_SPEED * 60.0)

    max_time = 0
    for obj in objects:
        obj_end = int(obj.time + obj.height)
        if obj_end > max_time:
            max_time = obj_end
    max_time += 10

    collisions_at_time = defaultdict(list)
    pickups_at_time = defaultdict(list)

    for obj in objects:
        t_start = int(obj.time)
        t_end = int(obj.time + obj.height)
        block_l = obj.x - eff_radius
        block_r = obj.x + obj.width + eff_radius
        for t in range(t_start, t_end + 1):
            if t > max_time:
                break
            collisions_at_time[t].append((block_l, block_r))

        if obj.move_speed != 0:
            t_pickup = min(int(obj.time + obj.height) + 1, max_time)
            pickups_at_time[t_pickup].append(obj.move_speed)

    reachable = [defaultdict(list) for _ in range(max_time + 1)]
    start_t = PLAY_START_FRAME
    reachable[start_t][1.0] = [(50.0, 50.0)]

    def merge_intervals(intervals):
        if not intervals:
            return []
        intervals = sorted(intervals)
        merged = [intervals[0]]
        for a, b in intervals[1:]:
            if a <= merged[-1][1] + 1e-9:
                merged[-1] = (merged[-1][0], max(merged[-1][1], b))
            else:
                merged.append((a, b))
        return merged

    def expand_by_dx(intervals, dx):
        if dx <= 0:
            return intervals
        return [(max(2.5, a - dx), min(97.5, b + dx)) for a, b in intervals]

    for t in range(start_t, max_time):
        if not reachable[t]:
            continue

        for ms, intervals in list(reachable[t].items()):
            max_dx = BASE_DX_PER_EDITOR_TIME * ms
            next_intervals = expand_by_dx(intervals, max_dx)

            nt = t + 1
            for block_l, block_r in collisions_at_time.get(nt, []):
                new_intervals = []
                for a, b in next_intervals:
                    if b <= block_l or a >= block_r:
                        new_intervals.append((a, b))
                    else:
                        if a < block_l:
                            new_intervals.append((a, min(b, block_l)))
                        if b > block_r:
                            new_intervals.append((max(a, block_r), b))
                next_intervals = new_intervals

            if not next_intervals:
                continue

            next_intervals = merge_intervals(next_intervals)

            pickup_ms = ms
            for delta_ms in pickups_at_time.get(nt, []):
                pickup_ms = ms + delta_ms
                pickup_ms = max(0.1, min(5.0, pickup_ms))
                break

            reachable[nt][pickup_ms].extend(next_intervals)

        for ms in reachable[t]:
            reachable[t][ms] = merge_intervals(reachable[t][ms])

    reachable_grid = [[False] * 101 for _ in range(max_time + 1)]
    for t in range(max_time + 1):
        if not reachable[t]:
            continue
        for ms, intervals in reachable[t].items():
            for a, b in intervals:
                ix0 = max(0, int(a))
                ix1 = min(100, int(b) + 1)
                for ix in range(ix0, ix1 + 1):
                    reachable_grid[t][ix] = True

    return reachable_grid, max_time


def draw_reachability(editor_state, reachable_grid, max_time):
    """Draw reachability overlay on editor_state.game.disp"""
    if gl is None:
        return

    surface = gl.pygame.Surface((500, 700), gl.pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))

    t_min = max(0, int((editor_state.time_offset * 5 - editor_state.player_y + PLAY_START_FRAME * 5) / 7))

    for t in range(t_min, 999999999):
        if t >= len(reachable_grid): break
        if not reachable_grid[t]:
            continue

        screen_y = (t - editor_state.time_offset) * 5 + (editor_state.player_y - PLAY_START_FRAME * 5)

        for x in range(101):
            if reachable_grid[t][x]:
                px = x * 5
                gl.pygame.draw.rect(surface, (0, 255, 0, 120), (px, screen_y, 5, 7))

    #px = 50 * 5 - PLAYER_SIZE / 2.0
    #py = editor_state.player_y - PLAYER_SIZE / 2.0
    #gl.pygame.draw.rect(surface, (255, 0, 0, 200), (px, py, PLAYER_SIZE, PLAYER_SIZE))

    editor_state.game.disp.blit(surface, (0, 0))

    if editor_state.reachability:
        label = f'Tolerance: {editor_state.reach_tolerance}px'
        tw, th = gl.textSize(label, 16)
        lx, ly = 250, TIMELINE_BAR_BOTTOM
        editor_state.reach_label_rect = (lx, ly, lx + tw, ly + th)
        gl.drawText(label, lx, ly, 16, (0, 255, 0))

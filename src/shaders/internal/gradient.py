#type:ignore

SCREEN_W = 100
SCREEN_H = 75

r1, g1, b1 = colors[0]
r2, g2, b2 = colors[1]

def to_linear(c):
    return (c / 255) ** 0.5

def to_srgb(c):
    return int((c ** 2) * 255)

def shader(color, x, y, frame):
    r1, g1, b1 = colors[0]
    r2, g2, b2 = colors[1]

    x_norm = x / SCREEN_W
    y_norm = y / SCREEN_H

    angle_rad = gl.radians(angle)
    dx = x_norm - 0.5
    dy = y_norm - 0.5

    gradient_pos = dx * gl.cos(angle_rad) + dy * gl.sin(angle_rad)
    max_dist = 0.5 * (abs(gl.cos(angle_rad)) + abs(gl.sin(angle_rad)))
    gradient_pos = (gradient_pos / max_dist) * 0.5 + 0.5
    gradient_pos = max(0, min(gradient_pos, 1))

    r1_lin = to_linear(r1)
    g1_lin = to_linear(g1)
    b1_lin = to_linear(b1)

    r2_lin = to_linear(r2)
    g2_lin = to_linear(g2)
    b2_lin = to_linear(b2)

    r_lin = r1_lin * (1 - gradient_pos) + r2_lin * gradient_pos
    g_lin = g1_lin * (1 - gradient_pos) + g2_lin * gradient_pos
    b_lin = b1_lin * (1 - gradient_pos) + b2_lin * gradient_pos

    r = to_srgb(r_lin)
    g = to_srgb(g_lin)
    b = to_srgb(b_lin)

    return gl.clamp_ints(r, g, b)

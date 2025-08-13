# type: ignore

def shader(color, x, y, frame, sprite):
    x -= cx
    y -= cy

    frame = frame * 0.01

    # Smooth, continuous color transition
    r = gl.sin(x * 0.1 + frame*3) * 70
    g = gl.sin(y * 0.1 + frame*2) * 70
    b = gl.sin((x + y) * 0.08 + frame) * 70

    return gl.clamp_ints(*gl.sum_ints((r, g, b), gl.sum_ints(color,(-100,-100,-100))))


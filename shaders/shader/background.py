# type: ignore

def shader(color, x, y, frame):
    x -= cx
    y -= cy

    # Precompute frame-based values
    frame = frame * 0.01

    # Smooth, continuous color transition
    r = gl.sin(x * 0.1 + frame*3) * 70
    g = gl.sin(y * 0.1 + frame*2) * 70
    b = gl.sin((x + y) * 0.08 + frame) * 70

    return gl.clamp_ints(r+100, g+100, b+100)



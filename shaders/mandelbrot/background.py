#type:ignore
from numba import njit

ONE_THIRD = 1.0 / 3.0
TWO_THIRD = 2.0 / 3.0
ONE_SIXTH = 1.0 / 6.0

@njit
def shader(color, x, y, frame, cx, cy, scale):
    # Apply panning
    x += cx
    y += cy

    # Apply zoom
    x *= scale
    y *= scale

    # Optimization 1: Early bailout for points likely in the set
    # Skip detailed calculation if clearly in main bulb or cardioid
    q = (x - 0.25)**2 + y**2
    if q*(q + (x - 0.25)) < 0.25*y**2 or (x + 1)**2 + y**2 < 0.0625:
        return (0, 0, 0)  # Definitely in the set

    c = complex(x, y)
    z = 0

    def hsl(h, s, l):
        h_norm = h / 360
        l_norm = l / 100
        s_norm = s / 100

        if s_norm == 0.0:
            rgb_val = l_norm
            return (int(rgb_val*255), int(rgb_val*255), int(rgb_val*255))

        if l_norm <= 0.5:
            m2 = l_norm * (1.0 + s_norm)
        else:
            m2 = l_norm + s_norm - (l_norm * s_norm)

        m1 = 2.0 * l_norm - m2

        # Define color conversion inline
        def value(hue):
            hue = hue % 1.0
            if hue < ONE_SIXTH:
                return m1 + (m2-m1)*hue*6.0
            if hue < 0.5:
                return m2
            if hue < TWO_THIRD:
                return m1 + (m2-m1)*(TWO_THIRD-hue)*6.0
            return m1

        r = value(h_norm + ONE_THIRD)
        g = value(h_norm)
        b = value(h_norm - ONE_THIRD)

        return (int(r*255), int(g*255), int(b*255))

    max_iter = 100
    # Optimization 3: Escape radius optimization (bail out earlier)
    for i in range(max_iter):
        z = z**2 + c
        if abs(z) > 2:
            # Optimization 4: Smooth coloring
            # Use log to create smooth transitions between iteration bands
            smooth_i = i + 1 - gl.log(gl.log(abs(z))) / gl.log(2)
            color_value = smooth_i / max_iter

            # Optimization 5: HSL color space for prettier results
            hue = (color_value * 360) % 360
            return hsl(hue, 80, 50)

    # Points in the set are black
    return (0, 0, 0)

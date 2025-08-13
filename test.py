import engine as gl

game = gl.Game('Test', (800,600), 8)
game.id = 'platformer'
game.version = 5

# Mandelbrot shader parameters
scale = 0.01
cx = 0
cy = 0

shader = gl.loadShaderFile('shaders/mandelbrot','background.py', globals())

if isinstance(shader, tuple):
    exit(f"{shader[0]}: {shader[1]}")

@game.on('frame')
def frame(frame):
    global cx, cy

    game.disp.fill((0, 0, 0))

    gl.drawRectShaded(
        (0, 0, game.disp.get_width()-10, game.disp.get_height()-10),
        shader,
        args=[cx, cy, scale]
    )    # Pan speed should be proportional to zoom level
    # Smaller scale = more zoomed in = more detail visible = slower panning needed
    # This makes navigation feel consistent at all zoom levels
    pan_speed = scale * 10000
    
    # Another way to think about it: pan by a consistent percentage of the visible area
    if gl.keyPressed('w'):
        cy -= pan_speed
    if gl.keyPressed('s'):
        cy += pan_speed
    if gl.keyPressed('a'):
        cx -= pan_speed
    if gl.keyPressed('d'):
        cx += pan_speed

@game.on('scroll')
def scroll(event):
    global scale, cx, cy

    # Prevent excessive zooming
    if scale < 0.000001 and event.get('y') > 0:  # Don't zoom in too far
        return
    if scale > 10 and event.get('y') < 0:  # Don't zoom out too far
        return

    # Get mouse position in pixels
    mouse_x, mouse_y = gl.pygame.mouse.get_pos()

    # Convert to logical coordinates (the coordinates in our game space)
    logical_mouse_x = mouse_x / game.res
    logical_mouse_y = mouse_y / game.res    # Calculate the fractal coordinates under the mouse BEFORE zooming
    # The shader does: x += cx; y += cy; x *= scale; y *= scale;
    # So the correct mapping is: fractal = (pixel + offset) * scale
    mouse_fractal_x = (logical_mouse_x + cx) * scale
    mouse_fractal_y = (logical_mouse_y + cy) * scale

    # Calculate new zoom level
    zoom_factor = 1.2
    old_scale = scale
    if event.get('y') > 0:
        # Zoom in
        new_scale = old_scale / zoom_factor
    else:
        # Zoom out
        new_scale = old_scale * zoom_factor

    # Now we need to solve for new cx, cy values that will keep
    # the point under the mouse at the same fractal coordinates
    # Equation: mouse_fractal_x = (logical_mouse_x + new_cx) * new_scale
    # Solving for new_cx:
    new_cx = (mouse_fractal_x / new_scale) - logical_mouse_x
    new_cy = (mouse_fractal_y / new_scale) - logical_mouse_y
    
    # Update the cx and cy values
    cx = new_cx
    cy = new_cy

    # Update the scale
    scale = new_scale
      # Print debug info with more detail
    print(f"Mouse: ({logical_mouse_x:.1f},{logical_mouse_y:.1f}) | Scale: {scale:.8f} | Fractal: ({mouse_fractal_x:.6f},{mouse_fractal_y:.6f}) | Offsets: ({cx:.6f},{cy:.6f})")

game.run()

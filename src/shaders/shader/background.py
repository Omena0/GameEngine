# type: ignore




def shader(color, x, y, frame):
    x += 100
    y += 100

    # Initial scramble
    frame = ((frame + 2 * x + (y * 9 % 28)) << 9) % 256
    frame = frame + x*y + (x**2 % (y+1)) - (y**2 % (x+1)) << 3
    frame = (frame + int(abs(gl.sin(frame*gl.pi) * 10000))) % 100000

    # Avalanche
    frame = (frame + x*y*31 + (x**2 + y**2)*17) % 100000
    frame = frame ^ ((frame * ((x+y)%23 + 1)) + (x*y + y**3 + x**3) % 97)
    frame = (frame * (x*19 + y*23 + 37)) % 100000
    frame = frame + ((frame // 7) * ((x^y)+1)) % 100000

    # This thing
    frame = frame + x*y + (x**2 % (y+1)) - (y**2 % (x+1))
    frame = frame * ((x+y)%7 + 1) + (y*x % 13)
    frame = (frame + (x*y*(x+y) % 31)) % 100000

    # After scramble
    frame = frame * ((x+y)%7 + 1) + (y*x % 13) ^ y
    frame = (frame + (x*y*(x+y) % 31)) % 100000

    r = gl.tan(x/(frame+1)*10000000)
    g = gl.cos(frame*10000000)
    b = gl.sin(y/(frame+1)*10000000)

    r *= x**3*y
    g *= y**4*x
    b *= x**2*y

    r %= 256
    g %= 256
    b %= 256

    r,g,b = gl.clamp_ints(r, g, b)

    return r,g,b



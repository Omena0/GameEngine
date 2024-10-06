import engine as gl

game = gl.Game("Game", (50,37), res=16, max_fps=0, bg = (255,255,255))

paddle1 = gl.Sprite(
    (2,13),
    [[(0, 0, (4-abs(y-5))*40+40) for y in range(11)]]
).add(game)

paddle2 = gl.Sprite(
    (47, 13),
    [[((4-abs(y-5))*30+50, 0, 0) for y in range(11)]]
).add(game)

ball = gl.Sprite(
    (10, 10),
    [[((y+1)*75 if x else 0, 0, 0 if x else (y+1)*75) for y in range(2)] for x in range(2)]
).add(game)

ball.vel = (1, 1)

@game.shader
def shader(col, x, y, frame, sprite):
    if not sprite:
        col = ((x+frame/10%10)*2, (y+frame/10%10)*2, (x+y+frame*2/10%10)*2)

    return col

@game.on("keyDown")
def move(key):
    if key == gl.pygame.K_w:
        paddle1.move((0, -1))
    elif key == gl.pygame.K_s:
        paddle1.move((0, 1))
    elif key == gl.pygame.K_UP:
        paddle2.move((0, -1))
    elif key == gl.pygame.K_DOWN:
        paddle2.move((0, 1))

@game.on("frame")
def frame(frame):
    if frame % 10 != 0:
        return
    ball.move(ball.vel)

    if ball.collides_with(paddle1) or ball.collides_with(paddle2):
        ball.vel = (-ball.vel[0], ball.vel[1])
        ball.move(ball.vel)

    elif ball.collides_with("edge"):
        ball.vel = (ball.vel[0], -ball.vel[1])
        ball.move(ball.vel)

        if ball.x < 0:
            game.running = False
            print('Red Wins!')
        elif ball.x > game.width:
            game.running = False
            print('Blue Wins!')

game.run()

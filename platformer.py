import engine as gl

jumpForce = 1.2
dashForce = 1.5
gravity = 0.03
acceleration = 30
max_speed = 0.7
air_resistance = 0.97
maxJumps = 2
maxDashes = 1

# Initialize the game
game = gl.Game("fr", (75,50),res=8,max_fps=120)

cx,cy = 0,0

# Add a player sprite
player_texture = [
    [(255, 0, 0), (255, 0, 0), (255, 0, 0)],
    [(255, 0, 0), (255, 0, 0), (255, 0, 0)],
    [(255, 0, 0), (255, 0, 0), (255, 0, 0)]
]

player = gl.Sprite((game.width // 2, game.height // 3*2), player_texture).add(game)

platforms = []

class Platform():
    def __init__(self, pos, width, height=3, attributes=None, shader = None):
        if attributes is None:
            attributes = {"bounciness": 1}

        self.pos = pos
        self.x = pos[0]
        self.y = pos[1]
        self.width = width
        self.height = height
        self.texture = [[shader() if shader else (255,255,255) for _ in range(self.height)] for _ in range(self.width)]
        self.sprite = gl.Sprite(self.pos, self.texture).add(game)

        for key,value in attributes.items():
            setattr(self.sprite, key, value)

        platforms.append(self.sprite)


Platform((35, 40), 50)
Platform((100, 30), 50)
Platform((60, 50), 50)




def updateCamera():
    global cx,cy
    if cy < -50:
        cy = -cy-30
    for sprite in game.sprites:
        if sprite == player:
            continue
        sprite.x = sprite.pos[0] + cx
        sprite.y = sprite.pos[1] + cy

@game.on('frame')
def frame(frame):
    global cx,cy, pressed, jumps, dashes

    vel[0] = round(vel[0],10)
    vel[1] = round(vel[1],10)

    vel[0] = vel[0]*air_resistance
    vel[1] = vel[1]*air_resistance


    cx += vel[0]
    cy += vel[1]

    if abs(vel[0]) < max_speed or vel[0] * pressed < 0:
        vel[0] += pressed/acceleration

    if platform := player.collides_with(platforms):
        jumps = maxJumps
        dashes = maxDashes
        platform = platform[0]
        vel[1] *= -platform.bounciness
        vel[1] = int(vel[1])

        while player.collides_with(platforms):
            cy += 0.01
            updateCamera()

        cy -= 0.015

    else:
        vel[1] -= gravity

    updateCamera()
    if frame % 10 == 0:
        print(f'X: {round(cx):<5} Y: {round(cy):<5} VX: {round(vel[0]):<5} VY: {round(vel[1]):<5}')

vel = [0,0]
pressed = 0

@game.on('keyDown')
def move(key):
    global cx, cy, pressed, jumps, dashes
    if key == gl.pygame.K_w:
        if jumps:
            jumps -= 1
            vel[1] += jumpForce
            cy += vel[1]
            updateCamera()

    elif key == gl.pygame.K_SPACE:
        if dashes:
            dashes -= 1
            if vel[0] > 0:
                vel[0] += dashForce
            else:
                vel[0] -= dashForce

            print(vel)
            updateCamera()

    elif key == gl.pygame.K_a:
        pressed += 1

    elif key == gl.pygame.K_d:
        pressed -= 1

    elif key == gl.pygame.K_q:
        game.running = False

@game.on('keyUp')
def move(key):
    global cx, cy, pressed
    if key == gl.pygame.K_a:
        pressed -= 1
    elif key == gl.pygame.K_d:
        pressed += 1

# Run the game
game.run()






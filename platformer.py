import engine as gl
from levelLoader import Level

jumpForce = 1.2
dashForce = 1.5
gravity = 0.03
acceleration = 30
max_speed = 0.7
air_resistance = 0.97
maxJumps = 2
maxDashes = 1

jumps = 0
dashes = 0
vel = [0,0]
pressedX = 0
pressedY = 0

flight = False
noclip = False
editor = False

startPos = None
editedObj = None

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
        self.shader = shader
        self.texture = self.gen_texture()
        self.sprite = gl.Sprite(self.pos, self.texture).add(game)

        for key,value in attributes.items():
            setattr(self.sprite, key, value)

        platforms.append(self.sprite)

    def gen_texture(self):
        self.texture = [[self.shader() if self.shader else (255,255,255) for _ in range(self.height)] for _ in range(self.width)]
        return self.texture

Platform((30,30), 20)

def updateCamera():
    global cx,cy
    if cy < -50:
        cy = -cy-30

    for sprite in game.sprites:
        if sprite == player:
            sprite.x = game.width // 2
            sprite.y = game.height // 3*2
            sprite.x -= vel[0]*2
            sprite.y -= vel[1]*2
            continue

        sprite.x = sprite.pos[0] + cx
        sprite.y = sprite.pos[1] + cy

@game.on('frame')
def frame(frame):
    global cx,cy, pressedX, jumps, dashes

    vel[0] = round(vel[0],10)
    vel[1] = round(vel[1],10)

    vel[0] = vel[0]*air_resistance
    vel[1] = vel[1]*air_resistance


    cx += vel[0]
    cy += vel[1]

    if abs(vel[0]) < max_speed or vel[0] * pressedX < 0:
        vel[0] += pressedX/acceleration

    if abs(vel[1]) < max_speed or vel[1] * pressedY < 0:
        vel[1] += pressedY/acceleration

    platform = player.collides_with(platforms)
    if platform and not noclip:
        jumps = maxJumps
        dashes = maxDashes
        platform = platform[0]
        vel[1] *= -platform.bounciness
        vel[1] = int(vel[1])

        while player.collides_with(platforms):
            cy += 0.01
            updateCamera()

        cy -= 0.015

    elif not flight:
        vel[1] -= gravity

    updateCamera()
    if frame % 10 == 0:
        print(f'X: {round(cx):<5} Y: {round(cy):<5} VX: {round(vel[0]):<5} VY: {round(vel[1]):<5}')

@game.on('mouseDown')
def mouseDown(event):
    global startPos, editedObj, editor
    if not editor: return
    pos = (event['pos'][0]//game.res-cx,event['pos'][1]//game.res-cy)
    startPos = pos
    editedObj = Platform(pos,1,1)

@game.on('mouseMove')
def mouseMove(event):
    global startPos, editedObj, editor
    if not editor: return
    if startPos and editedObj:
        pos = (event['pos'][0]//game.res-cx,event['pos'][1]//game.res-cy)
        width = int(pos[0]-startPos[0])
        height = int(pos[1]-startPos[1])
        editedObj.width = max(width,1)
        editedObj.height = max(height,1)
        print(editedObj.width,editedObj.height)
        editedObj.sprite.updateTexture(editedObj.gen_texture())


@game.on('mouseUp')
def mouseUp(event):
    global startPos, editedObj, editor
    if not editor: return
    startPos = None
    editedObj = None

@game.on('keyDown')
def keyDown(key):
    key = key['key']
    global cx, cy, pressedX, pressedY, jumps, dashes, flight, noclip, editor
    if key == gl.pygame.K_w:
        pressedY += 1
        if flight:
            cy += 1

        elif jumps:
            jumps -= 1
            vel[1] += jumpForce
            cy += vel[1]
            updateCamera()

    elif key == gl.pygame.K_s:
        pressedY -= 1

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
        pressedX += 1

    elif key == gl.pygame.K_d:
        pressedX -= 1

    elif key == gl.pygame.K_q:
        game.running = False

    elif key == gl.pygame.K_f:
        flight = not flight

    elif key == gl.pygame.K_c:
        noclip = not noclip

    elif key == gl.pygame.K_e:
        editor = not editor
        flight = editor

@game.on('keyUp')
def keyUp(key):
    key = key['key']
    global cx, cy, pressedX, pressedY
    if key == gl.pygame.K_a:
        pressedX -= 1
    elif key == gl.pygame.K_d:
        pressedX += 1
    elif key == gl.pygame.K_w:
        pressedY -= 1
    elif key == gl.pygame.K_s:
        pressedY += 1

# Run the game
game.run()






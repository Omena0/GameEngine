from levelLoader import Level
from ast import literal_eval
import engine as gl

def convert_type(s):
    try:
        return literal_eval(s)
    except:
        return s

### [Vars/Physics]
jumpForce = 1
dashForce = 1.5
gravity = 0.03
acceleration = 30
max_speed = 0.7
air_resistance = 0.97
maxJumps = 2
maxDashes = 1

### [Vars/Init]
jumps = 0
dashes = 0
vel = [0,0]
pressedX = 0
pressedY = 0

### [Vars/Flags]
flight = False
noclip = False
editor = False

### [Vars/Editor]
mode = None
startPos = None
editedObj = None
selectedObj = None

### [Vars/Level]
objects = []
meta = {"name": "Unnamed", "description": "No description"}

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

### [Object()]
class Object:
    def __init__(self, pos, width, height, attributes, shader = None):
        self.x = int(pos[0])
        self.y = int(pos[1])
        self.pos = self.x,self.y
        self.width = width
        self.height = height
        self.shader = shader
        self.attributes = attributes
        self.texture = self.gen_texture()
        self.sprite = gl.Sprite(self.pos, self.texture).add(game)

        self.sprite.object = self

        objects.append(self.sprite)

        for key,value in attributes.items():
            setattr(self.sprite, key, value)

### [Platform(Object)]
class Platform(Object):
    def __init__(self, pos, width, height=3, attributes=None, shader = None):
        if attributes is None:
            attributes = {"bounciness": 1.1}

        super().__init__(pos, width, height, attributes, shader)
        self.sprite.platform = self

    def gen_texture(self):
        self.texture = [[self.shader() if self.shader else (255,255,255) for _ in range(self.height)] for _ in range(self.width)]
        return self.texture

Platform((30,30), 20)

### [updateCamera()]
def updateCamera():
    global cx,cy
    if cy < -50:
        cy = -cy-30

    for sprite in game.sprites:
        if sprite == player:
            sprite.x = game.width // 2
            sprite.y = game.height // 3*2
            sprite.x -= vel[0]*2
            sprite.y -= vel[1]*3
            continue

        sprite.x = sprite.pos[0] + cx
        sprite.y = sprite.pos[1] + cy

### [GameLoop/Event]
@game.on('frame')
def frame(frame):
    global cx,cy, pressedX, jumps, dashes

    ### [GameLoop/Apply velocity]
    vel[0] = round(vel[0],10)
    vel[1] = round(vel[1],10)

    vel[0] = vel[0]*air_resistance
    vel[1] = vel[1]*air_resistance

    cx += vel[0]
    cy += vel[1]

    ### [GameLoop/Apply movement]
    if abs(vel[0]) < max_speed or vel[0] * pressedX < 0:
        vel[0] += pressedX/acceleration

    if abs(vel[1]) < max_speed or vel[1] * pressedY < 0:
        vel[1] += pressedY/acceleration

    ### [GameLoop/Collisions]
    platform = player.collides_with(objects)
    if platform and not noclip:
        jumps = maxJumps
        dashes = maxDashes
        platform = platform[0]
        vel[1] *= -platform.bounciness
        vel[1] = int(vel[1])

        while player.collides_with(objects):
            cy += 0.01
            updateCamera()

        cy -= 0.015

    ### [GameLoop/Gravity]
    elif not flight:
        vel[1] -= gravity

    ### [GameLoop/Camera]
    updateCamera()
    #if frame % 10 == 0:
    #    print(f'X: {round(cx):<5} Y: {round(cy):<5} VX: {round(vel[0]):<5} VY: {round(vel[1]):<5}')

### [Editor Mouse]
@game.on('mouseDown')
def mouseDown(event):
    global startPos, grabPos, editedObj, editor, mode
    if not editor: return
    pos = (event['pos'][0]//game.res-cx, event['pos'][1]//game.res-cy)
    pos = round(pos[0]), round(pos[1])

    if event['button'] == 1:
        startPos = pos
        mode = 'add'
        editedObj = Platform(pos,1,1)

    elif event['button'] == 2:
        for sprite in objects:
            if sprite.collidepoint(pos):
                startPos = sprite.pos[0]+sprite.width-1, sprite.pos[1]+sprite.height-1
                grabPos = sprite.pos[0]-pos[0], sprite.pos[1]-pos[1]
                mode = 'edit'
                editedObj = sprite.platform
                break

    elif event['button'] == 3:
        for sprite in objects:
            if sprite.collidepoint(pos):
                startPos = pos
                grabPos = sprite.pos[0]-pos[0], sprite.pos[1]-pos[1]
                mode = 'move'
                editedObj = sprite.platform
                break

@game.on('mouseMove')
def mouseMove(event):
    global startPos, editedObj, editor, mode
    if not editor: return
    if startPos and editedObj and mode:
        pos = (event['pos'][0]//game.res-cx,event['pos'][1]//game.res-cy)
        pos = round(pos[0]), round(pos[1])

        if mode == 'add':
            width = int(pos[0]-startPos[0])+1
            height = int(pos[1]-startPos[1])+1
            editedObj.width = max(width,1)
            editedObj.height = max(height,1)
            editedObj.sprite.updateTexture(editedObj.gen_texture())

        elif mode == 'edit':
            pos = int(pos[0]+grabPos[0]), int(pos[1]+grabPos[1])
            editedObj.x = pos[0]
            editedObj.y = pos[1]
            editedObj.pos = pos
            editedObj.sprite.pos = pos

            width = startPos[0]-pos[0]
            height = startPos[1]-pos[1]

            editedObj.width = max(width,1)
            editedObj.height = max(height,1)
            editedObj.sprite.updateTexture(editedObj.gen_texture())

        elif mode == 'move':
            pos = int(pos[0]+grabPos[0]), int(pos[1]+grabPos[1])
            editedObj.x = pos[0]
            editedObj.y = pos[1]
            editedObj.pos = pos
            editedObj.sprite.pos = pos

@game.on('mouseUp')
def mouseUp(event):
    global startPos, editedObj, editor, mode
    if not editor: return
    mode = None
    startPos = None
    editedObj = None

### [Keyboard Events/Event]
@game.on('keyDown')
def keyDown(key):  # sourcery skip: low-code-quality
    key = key['key']
    global cx, cy, pressedX, pressedY, jumps, dashes, flight, noclip, editor, meta, objects
    ### [Keyboard Events/w]
    if key == gl.pygame.K_w:
        pressedY += 1
        if flight:
            cy += 1

        elif jumps:
            jumps -= 1
            vel[1] += jumpForce
            cy += vel[1]
            updateCamera()

    ### [Keyboard Events/s]
    elif key == gl.pygame.K_s:
        pressedY -= 1

    ### [Keyboard Events/Space]
    elif key == gl.pygame.K_SPACE:
        if dashes:
            dashes -= 1
            if vel[0] > 0:
                vel[0] += dashForce
            else:
                vel[0] -= dashForce

            print(vel)
            updateCamera()

    ### [Keyboard Events/a]
    elif key == gl.pygame.K_a:
        pressedX += 1

    ### [Keyboard Events/d]
    elif key == gl.pygame.K_d:
        pressedX -= 1

    ### [Keyboard Events/q]
    elif key == gl.pygame.K_q:
        game.running = False

    ### [Keyboard Events/f]
    elif key == gl.pygame.K_f:
        flight = not flight

    ### [Keyboard Events/c]
    elif key == gl.pygame.K_c:
        noclip = not noclip

    ### [Keyboard Events/e]
    elif key == gl.pygame.K_e:
        editor = not editor
        flight = editor

    ### [Keyboard Events/o]
    elif key == gl.pygame.K_o:
        Level('level.txt').save_level(meta, objects)
    
    ### [Keyboard Events/l]
    elif key == gl.pygame.K_l:
        for sprite in objects:
            if sprite == player: continue
            game.sprites.remove(sprite)

        objects = []

        meta, newObjects = Level('level.txt').load_level()
        for object in newObjects:
            x,y,width,height,attr,texture = object
            x,y,width,height = int(x),int(y),int(width),int(height)
            attr = dict([(i.split('=')[0], convert_type(i.split('=')[1])) for i in attr.split(',')])
            texture = convert_type(texture)

            object = Platform((x,y),width,height,attr)
            object.sprite.updateTexture(texture)

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


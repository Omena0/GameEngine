from levelLoader import Level
from ast import literal_eval
import engine as gl
gl.pygame.init()

def convert_type(s):
    try:
        return literal_eval(s)
    except:
        return s

### [Vars/Physics]
jumpForce = 0.9
dashForce = 0.8
gravity = 0.03
acceleration = 40
max_speed = 0.6
air_resistance = 0.98
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
game = gl.Game("Platformer", (75,50),res=8,max_fps=120)

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
            attributes = {"bounciness": 1.1, "physics": True}

        super().__init__(pos, width, height, attributes, shader)
        self.sprite.platform = self

    def gen_texture(self):
        self.texture = [[self.shader() if self.shader else (255,255,255) for _ in range(self.height)] for _ in range(self.width)]
        return self.texture

# Spawns a platform so you dont fall into the void instantly
Platform((30,30), 20)

### [updateCamera()]
def updateCamera():
    global cx,cy
    if cy <= -150:
        cy = -cy
        cx = 0

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
    platforms = player.collides_with(objects)
    if platforms and not noclip:
        for platform in platforms:
            if not getattr(platform, 'physics', True):
                continue

            jumps = maxJumps
            dashes = maxDashes
            vel[1] *= -platform.bounciness
            vel[1] = int(vel[1])

            while player.collides_with(objects):
                cy += 0.01
                updateCamera()

            cy -= 0.015

    ### [GameLoop/Gravity]
    if not flight:
        vel[1] -= gravity

    ### [GameLoop/Camera]
    updateCamera()

    font = gl.pygame.font.SysFont('FreeSans',20,True)
    surf = font.render(meta['name'],1,(255,255,255))
    game.screen.blit(surf,(5,5))

    font = gl.pygame.font.SysFont('FreeSans',12,False)
    surf = font.render(meta['description'],1,(255,255,255))
    game.screen.blit(surf,(10,30))

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
        if flight:
            pressedY += 1
            cy += 1

        elif jumps:
            jumps -= 1
            vel[1] += jumpForce
            cy += vel[1]
            updateCamera()

    ### [Keyboard Events/s]
    elif key == gl.pygame.K_s:
        if flight:
            pressedY -= 1

    ### [Keyboard Events/Space]
    elif key == gl.pygame.K_SPACE:
        if dashes:
            dashes -= 1
            if vel[0] > 0:
                vel[0] += dashForce
            else:
                vel[0] -= dashForce

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

    ### [Keyboard Events/p]
    elif key == gl.pygame.K_p:
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

    ### [Keyboard Events/delete]
    elif key == gl.pygame.K_DELETE:
        if not editor: return
        mouse_pos = gl.pygame.mouse.get_pos()
        pos = (mouse_pos[0]//game.res-cx,mouse_pos[1]//game.res-cy)
        pos = round(pos[0]), round(pos[1])

        for sprite in objects:
            if sprite.collidepoint(pos):
                game.sprites.remove(sprite)
                objects.remove(sprite)
                break

    ### [Keyboard Events/c]
    elif key == gl.pygame.K_c:
        if not editor: return
        mouse_pos = gl.pygame.mouse.get_pos()
        pos = (mouse_pos[0]//game.res-cx,mouse_pos[1]//game.res-cy)
        pos = round(pos[0]), round(pos[1])

        for sprite in objects:
            if sprite.collidepoint(pos):
                setattr(sprite, 'physics', not getattr(sprite, 'physics', True))
                sprite.object.attributes['physics'] = getattr(sprite, 'physics')
                print(sprite.object.attributes['physics'])

@game.on('keyUp')
def keyUp(key):
    key = key['key']
    global cx, cy, pressedX, pressedY
    if key == gl.pygame.K_a:
        pressedX -= 1
    elif key == gl.pygame.K_d:
        pressedX += 1
    elif key == gl.pygame.K_w:
        if flight:
            pressedY -= 1
    elif key == gl.pygame.K_s:
        if flight:
            pressedY += 1

# Run the game
game.run()


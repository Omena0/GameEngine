from tkinter import colorchooser
from levelLoader import Level
from ast import literal_eval
import engine as gl
import time as t
gl.pygame.init()


def convert_type(s):
    try:
        return literal_eval(s)
    except:
        return s

### [Vars/Physics]
jumpForce = 0.9
dashForce = 0.8
gravity = 0.04
acceleration = 40
max_speed = 0.7
air_resistance = 0.98
friction = 0.97
maxJumps = 2
maxDashes = 1

### [Vars/Init]
jumps = 0
dashes = 0
vel = [0,0]
pressedX = 0
pressedY = 0
startTime = 0
time = 0

### [Vars/Flags]
flight  = False
noclip  = False
editor  = False
help    = False
paint = False

normalHelp = """--- Movement ---
w - Jump/Up
a - Left
s - Down
d - Right
space - Dash

--- General ---
q - Quit
f  - Fly
n - Noclip
e - Editor
h - Help
p - Paint"""

editorHelp = """--- Editor ---
Left Mouse      - Create object (drag)
Right Mouse   - Move object (drag)
Middle Mouse - Resize object (drag)

-- Paint Mode --
Left Mouse - Paint
Left Mouse + Ctrl - Floodfill

c - Toggle object physics

ctrl + s - Save
ctrl + l  - Load
ctrl + c - Copy
ctrl + v - Paste
delete  - Delete"""

### [Vars/Editor]
mode = None
startPos = None
editedObj = None
selectedObj = None
clipboard = None
selectedCol = (0,255,0)


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
            attributes = {"bounciness": 0.8, "physics": True, "friction": 0.97}

        super().__init__(pos, width, height, attributes, shader)
        self.sprite.platform = self

    def gen_texture(self):
        self.texture = [[self.shader() if self.shader else (255,255,255) for _ in range(self.height)] for _ in range(self.width)]
        return self.texture

    def setPos(self, x, y):
        self.sprite.setPos(x,y)
        self.pos = x,y
        self.sprite.x = x
        self.sprite.y = y
        self.x = x
        self.y = y
        updateCamera()

# Spawns a platform so you dont fall into the void instantly
Platform((30,30), 20)

### [Utils]
def updateCamera():
    global cx,cy,vel,time
    if cy <= -100:
        cy = 0
        cx = 0
        vel = [0,0]
        time = None

    for sprite in game.sprites:
        if sprite == player:
            sprite.x = game.width // 2
            sprite.y = game.height // 3*2
            sprite.x -= vel[0]*2
            sprite.y -= vel[1]*3
            continue

        sprite.x = sprite.pos[0] + cx
        sprite.y = sprite.pos[1] + cy

def drawText(text:str,x:int,y:int,size=10,color=(255,255,255),bold=False,italic=False):
    font = gl.pygame.font.SysFont('FreeSans',size,bold,italic)
    i = 0
    for line in text.splitlines():
        if line:
            surf = font.render(line,1,color)
            game.screen.blit(surf,(x,y+size*i))
            i += 1.1
        else:
            i += 0.5

def floodfill(texture, pos, newColor, oldColor):
    if texture[pos[0]][pos[1]] != oldColor: return
    texture[pos[0]][pos[1]] = newColor

    if pos[0] > 0: floodfill(texture, (pos[0]-1, pos[1]), newColor, oldColor)
    if pos[0] < len(texture)-1: floodfill(texture, (pos[0]+1, pos[1]), newColor, oldColor)
    if pos[1] > 0: floodfill(texture, (pos[0], pos[1]-1), newColor, oldColor)
    if pos[1] < len(texture[0])-1: floodfill(texture, (pos[0], pos[1]+1), newColor, oldColor)

### [GameLoop/Event]
@game.on('frame')
def frame(frame):  # sourcery skip: low-code-quality
    global cx,cy, pressedX, jumps, dashes, time

    ### [GameLoop/Apply velocity]
    vel[0] = round(vel[0],10)
    vel[1] = round(vel[1],10)

    vel[0] = vel[0]*air_resistance
    vel[1] = vel[1]*air_resistance

    cx += vel[0]
    cy += vel[1]

    ### [GameLoop/Apply friction]
    platforms = player.collides_with(objects)
    if platforms and not noclip:
        for platform in platforms:
            if not getattr(platform, 'physics', True):
                continue
            vel[0] = vel[0]*getattr(platform,'friction',friction)
            vel[1] = vel[1]*getattr(platform,'friction',friction)

            if platform.texture[0][0] == (0,255,0) and not time:
                time = round(t.time()-startTime,2)

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

    drawText(meta['name'], 5, 5, 20)
    drawText(meta['description'], 10, 30, 12)

    modeText = f'Mode: {'Editor - ' if editor else ""}{mode or "None"}'
    drawText(modeText, 5, 50, 13)

    if noclip:
        drawText('Noclip: ON', 5, 70, 13)
    else:
        drawText('Noclip: OFF', 5, 70, 13)

    if flight:
        drawText('Flight: ON', 5, 90, 13)
    else:
        drawText('Flight: OFF', 5, 90, 13)

    if paint:
        drawText('Paint: ON', 5, 110, 13)
    else:
        drawText('Paint: OFF', 5, 110, 13)

    if time:
        drawText(f'Level completed in {time} seconds.', 5, 130, 13)
    else:
        drawText(f'Timer: {round(t.time()-startTime,2) if startTime else 0}', 5, 130, 13)

    if help:
        if editor:
            drawText(editorHelp, 5, 150, 15)
        else:
            drawText(normalHelp, 5, 150, 15)


### [Editor Mouse]
@game.on('mouseDown')
def mouseDown(event):  # sourcery skip: low-code-quality
    global startPos, grabPos, editedObj, editor, mode, selectedCol, oldTexture
    if not editor: return
    pos = (event['pos'][0]//game.res-cx, event['pos'][1]//game.res-cy)
    pos = round(pos[0]), round(pos[1])

    if event['button'] == 1:
        if paint and editor:
            if not selectedCol: return
            for sprite in objects:
                if sprite.collidepoint(pos):
                    startPos = pos[0]-sprite.pos[0], pos[1]-sprite.pos[1]

                    # Rectangle mode
                    if gl.pygame.key.get_mods() & gl.pygame.KMOD_CTRL:
                        col = sprite.texture[startPos[0]][startPos[1]]

                        floodfill(sprite.texture, startPos, selectedCol, col)

                    # Pixel mode
                    else:
                        sprite.texture[startPos[0]][startPos[1]] = selectedCol
                    break
        else:
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
                if paint and editor:
                    startPos = pos[0]-sprite.pos[0], pos[1]-sprite.pos[1]
                    sprite.texture[startPos[0]][startPos[1]] = game.bg

                else:
                    startPos = pos
                    grabPos = sprite.pos[0]-pos[0], sprite.pos[1]-pos[1]
                    mode = 'move'
                    editedObj = sprite.platform
                    break

@game.on('mouseMove')
def mouseMove(event):  # sourcery skip: low-code-quality
    global startPos, editedObj, editor, mode, oldTexture
    if not editor: return
    if startPos and editedObj and mode:
        pos = (event['pos'][0]//game.res-cx,event['pos'][1]//game.res-cy)
        pos = round(pos[0]), round(pos[1])

        if mode == 'add':
            width = int(pos[0]-startPos[0])+1
            height = int(pos[1]-startPos[1])+1

            if width < 1:
                editedObj.setPos(pos[0], editedObj.y)
                width = startPos[0]-pos[0]

            editedObj.width = max(width,1)

            if height < 1:
                editedObj.setPos(editedObj.x, pos[1])
                height = startPos[1]-pos[1]

            editedObj.height = max(height,1)

            editedObj.sprite.updateTexture(editedObj.gen_texture())

        elif mode == 'edit':
            pos = int(pos[0]+grabPos[0]), int(pos[1]+grabPos[1])
            editedObj.setPos(*pos)

            width = startPos[0]-pos[0]
            height = startPos[1]-pos[1]

            editedObj.width = max(width,1)
            editedObj.height = max(height,1)
            editedObj.sprite.updateTexture(editedObj.gen_texture())

        elif mode == 'move':
            pos = int(pos[0]+grabPos[0]), int(pos[1]+grabPos[1])
            editedObj.setPos(*pos)

@game.on('mouseUp')
def mouseUp(event):
    global startPos, editedObj, editor, mode
    if not editor: return
    mode = None
    startPos = None
    editedObj = None

### [Keyboard Events]
@game.on('keyDown')
def keyDown(key):  # sourcery skip: low-code-quality
    key = key['key']
    global cx, cy, pressedX, pressedY, jumps, dashes, flight, noclip, editor
    global meta, objects, clipboard, help, paint, selectedCol, startTime

    if not startTime and key in {gl.pygame.K_w,gl.pygame.K_a,gl.pygame.K_s,gl.pygame.K_d,gl.pygame.K_SPACE,gl.pygame.K_UP}:
        startTime = t.time()

    match key:
        case gl.pygame.K_w:
            if flight:
                pressedY += 1
                cy += 1

            elif jumps:
                jumps -= 1
                vel[1] += jumpForce
                cy += vel[1]
                updateCamera()

        case gl.pygame.K_UP:
            if jumps:
                jumps -= 1
                vel[1] += jumpForce
                cy += vel[1]
                updateCamera()

        case gl.pygame.K_s:
            if editor and gl.pygame.key.get_mods() & gl.pygame.KMOD_CTRL:
                Level('level.txt').save_level(meta, objects)
                print('Saved level')

            elif flight:
                pressedY -= 1

        case gl.pygame.K_SPACE:
            if dashes:
                dashes -= 1
                if vel[0] > 0:
                    vel[0] += dashForce
                else:
                    vel[0] -= dashForce

                updateCamera()

        case gl.pygame.K_a:
            pressedX += 1

        case gl.pygame.K_d:
            pressedX -= 1

        case gl.pygame.K_q:
            game.running = False

        case gl.pygame.K_f:
            flight = not flight

        case gl.pygame.K_n:
            noclip = not noclip

        case gl.pygame.K_e:
            editor = not editor
            flight = editor

        case gl.pygame.K_l:
            if not gl.pygame.key.get_mods() & gl.pygame.KMOD_CTRL: return

            for sprite in objects:
                if sprite == player: continue
                game.sprites.remove(sprite)

            objects = []

            meta, newObjects = Level('level.txt').load_level()
            for object in newObjects:
                x,y,width,height,attr,paint = object
                x,y,width,height = int(x),int(y),int(width),int(height)
                attr = dict([(i.split('=')[0], convert_type(i.split('=')[1])) for i in attr.split(',')])
                paint = convert_type(paint)

                object = Platform((x,y),width,height,attr)
                object.sprite.updateTexture(paint)

        case gl.pygame.K_DELETE:
            if not editor: return
            mouse_pos = gl.pygame.mouse.get_pos()
            pos = (mouse_pos[0]//game.res-cx,mouse_pos[1]//game.res-cy)
            pos = round(pos[0]), round(pos[1])

            for sprite in objects:
                if sprite.collidepoint(pos):
                    game.sprites.remove(sprite)
                    objects.remove(sprite)
                    break

        case gl.pygame.K_c:
            if not editor: return
            mouse_pos = gl.pygame.mouse.get_pos()
            pos = (mouse_pos[0]//game.res-cx,mouse_pos[1]//game.res-cy)
            pos = round(pos[0]), round(pos[1])


            for sprite in objects:
                if sprite.collidepoint(pos):
                        if gl.pygame.key.get_mods() & gl.pygame.KMOD_CTRL:
                            clipboard = [sprite.pos[0]-pos[0], sprite.pos[1]-pos[1], sprite.width,sprite.height,sprite.object.attributes,sprite.texture]

                        else:
                            setattr(sprite, 'physics', not getattr(sprite, 'physics', True))
                            sprite.object.attributes['physics'] = getattr(sprite, 'physics')
                            print(sprite.object.attributes['physics'])
                        break

        case gl.pygame.K_v:
            if not editor: return
            mouse_pos = gl.pygame.mouse.get_pos()
            pos = (mouse_pos[0]//game.res-cx,mouse_pos[1]//game.res-cy)
            pos = round(pos[0]), round(pos[1])

            if gl.pygame.key.get_mods() & gl.pygame.KMOD_CTRL and clipboard:
                x,y,width,height,attributes,paint = clipboard
                object = Platform((pos[0]+x,pos[1]+y),width,height,attributes)
                object.sprite.updateTexture(paint)

        case gl.pygame.K_h:
            help = not help

        case gl.pygame.K_p:
            if gl.pygame.key.get_mods() & gl.pygame.KMOD_CTRL:
                selectedCol = colorchooser.askcolor(selectedCol, title = "Select Color")[0]
            else:
                paint = not paint

@game.on('keyUp')
def keyUp(key):
    key = key['key']
    global cx, cy, pressedX, pressedY
    if key == gl.pygame.K_a and pressedX:
        pressedX -= 1
    if key == gl.pygame.K_d and pressedX:
        pressedX += 1
    if key == gl.pygame.K_w and pressedY and flight:
        pressedY -= 1
    if key == gl.pygame.K_s and pressedY and flight:
        pressedY += 1

# Run the game
game.run()


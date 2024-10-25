from tkinter import colorchooser, filedialog
from levelLoader import Level
from ast import literal_eval
import engine as gl
import pygame_textinput
import time as t
import math

gl.pygame.init()

def sigmoidf(x):
    return 1 / (1 + math.exp(-x))

def convert_type(s):
    try:
        return literal_eval(s)
    except:
        return s

### [Vars/Physics]
jumpForce = 0.8
gBendAmount = 4
gAccelerationAmount = 5
cameraFollowDistance = 4
universalPrecision = 5
dashForce = 0.85
gravity = 0.04
acceleration = 20
max_speed = 1.2
air_resistance = 0.99
friction = 0.97
maxJumps = 2
maxDashes = 1
parachuteResistance = 0.9

### [Vars/Init]
jumps = 0
dashes = 0
vel = [0,0]
pressedX = 0
pressedY = 0
startTime = 0
finishTime = 0
parachute = False

### [Vars/Flags]
flight   = False
noclip   = False
editor   = False
help     = False
paint    = False
debug    = False
typing   = False
onGround = False
hide_gui = False

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
p - Paint
r - Reset"""

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
game = gl.Game("Platformer", (75,50),res=8,max_fps=62)

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
    def __init__(self, type, pos, width, height, attributes, shader = None):
        self.type = type
        self.x = int(pos[0])
        self.y = int(pos[1])
        self.pos = self.x,self.y
        self.width = width
        self.height = height
        self.shader = shader
        self.attributes = attributes

        if hasattr(self,'gen_texture'):
            self.texture = self.gen_texture()
            self.sprite = gl.Sprite(self.pos, self.texture).add(game)
        else:
            self.texture = [[]]
            self.sprite = gl.Sprite(self.pos, self.texture, self.render).add(game)


        self.sprite.object = self

        objects.append(self.sprite)

        for key,value in attributes.items():
            setattr(self.sprite, key, value)

### [Platform(Object)]
class Platform(Object):
    def __init__(self, pos, width, height=3, attributes=None, shader = None):
        if attributes is None:
            attributes = {"bounciness": 0.5, "physics": True, "friction": friction}

        super().__init__('platform', pos, width, height, attributes, shader)
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

### [Text(Object)]
class Text(Object):
    def __init__(self, pos, text, size=10, color=(255,255,255), bold=False, italic=False, input=False):
        self.input = input
        self.attributes = {"text": text, "size": size, "color": color, "bold": bold, "italic": italic, "physics": False}
        super().__init__('text', pos, *gl.textSize(text, size), self.attributes, None)
        self.sprite.text = self

        if self.input:
            self.textinput = pygame_textinput.TextInputManager()
            @game.on('scroll')
            def scroll(event):
                y = int(event['y'])
                self.attributes['size'] += y

            if 'all' in game.events:
                game.events['all'].append(self.textinput.update)
            else:
                game.events['all'] = [self.textinput.update]

    def render(self):
        if self.input and not typing:
            self.attributes['text'] = self.textinput.value
            game.events['all'].remove(self.textinput.update)
            del self.textinput
            self.input = False

        if self.input:
            self.attributes['text'] = f'{self.textinput.left}|{self.textinput.right}'

        gl.drawText(self.attributes['text'], self.sprite.x*game.res, self.sprite.y*game.res, self.attributes['size'], self.attributes['color'], self.attributes['bold'], self.attributes['italic'])

# Spawns a platform so you dont fall into the void instantly
Platform((30,30), 20)

### [Utils]
def respawn():
    global cx,cy,vel,startTime
    cy = 0
    cx = 0
    vel = [0,0]
    startTime = None
    toast('You died.')

def updateCamera():
    global cx,cy,vel,startTime
    if cy <= -60:
        respawn()

    # Player movement
    player.x = game.width // 2
    player.y = game.height // 3*2

    dx = vel[0]*cameraFollowDistance
    dy = vel[1]*(cameraFollowDistance+1)

    player.x -= dx
    player.y -= dy

    # Object movement
    for sprite in objects:
        sprite.x = sprite.pos[0] + cx
        sprite.y = sprite.pos[1] + cy

def toast(text):
    gl.Toast((game.width*game.res-5,game.height*game.res-5),text,20)

### [GameLoop/Event]
@game.on('frame')
def frame(frame):  # sourcery skip: low-code-quality
    global cx,cy, pressedX, jumps, dashes, finishTime, startTime, onGround

    ### [GameLoop/Apply velocity]
    vel[0] = vel[0] * (parachuteResistance if parachute else air_resistance)
    vel[1] = vel[1] * (parachuteResistance if parachute else air_resistance)

    cx += vel[0]
    cy += vel[1]

    ## [GameLoop/Check movement]
    pressedX = 0
    pressedY = 0
    if not (gl.modPressed('shift') or gl.modPressed('ctrl')):
        if gl.keyPressed('w'):
            pressedY -= 1
        if gl.keyPressed('a'):
            pressedX += 1
        if gl.keyPressed('s'):
            pressedY += 1
        if gl.keyPressed('d'):
            pressedX -= 1

    ### [GameLoop/Apply movement]
    if abs(vel[0]) < max_speed or vel[0] * pressedX < 0:
        vel[0] += pressedX/acceleration

    if (abs(vel[1]) < max_speed or vel[1] * pressedY < 0) and flight:
        vel[1] += pressedY/acceleration

    if (pressedX or pressedY) and not startTime:
        startTime = t.time()

    ### [GameLoop/Collisions]
    onGround = False
    collisions = player.collides_with(objects)
    if collisions and not noclip:
        for sprite in collisions:
            object = sprite.object
            if object.type != 'platform':
                continue

            if not getattr(sprite, 'physics', True):
                continue

            onGround = True

            vel[0] = vel[0]*getattr(sprite,'friction',friction)
            vel[1] = vel[1]*getattr(sprite,'friction',friction)

            if sprite.texture[0][0] == (0,255,0) and not finishTime:
                finishTime = t.time()-startTime
                toast(f'Level competed in {finishTime} Seconds.')

            jumps = maxJumps
            dashes = maxDashes
            vel[1] *= -sprite.bounciness
            vel[1] = int(vel[1])

            collisions = player.collides_with(objects)
            for sprite in collisions:
                if not getattr(sprite, 'physics', True): continue
                while player.collides_with(sprite):
                    cy += 0.01
                    updateCamera()

            cy -= 0.015

    ### [GameLoop/Gravity]
    if not flight and not onGround:
        g = round(gravity * (-pressedY/gBendAmount+1+(-vel[1]/gAccelerationAmount)),3) * (0.5 if parachute else 1)
        vel[1] -= g

    # Round pos and vel
    vel[0] = round(vel[0], universalPrecision)
    vel[1] = round(vel[1], universalPrecision)

    cx = round(cx, universalPrecision)
    cy = round(cy, universalPrecision)

    if abs(vel[0]) < 0.01: vel[0] = 0
    if abs(vel[1]) < 0.01: vel[1] = 0

    ### [GameLoop/Camera]
    updateCamera()

    # GUI
    if not hide_gui:
        gl.drawText(meta['name'], 5, 5, 20)
        gl.drawText(meta['description'], 10, 30, 12)

        modeText = f'Mode: {'Editor - ' if editor else ""}{mode or "None"}'
        gl.drawText(modeText, 5, 50, 13)

        if noclip:
            gl.drawText('Noclip: ON', 5, 70, 13)
        else:
            gl.drawText('Noclip: OFF', 5, 70, 13)

        if flight:
            gl.drawText('Flight: ON', 5, 90, 13)
        else:
            gl.drawText('Flight: OFF', 5, 90, 13)

        if paint:
            gl.drawText('Paint: ON', 5, 110, 13)
        else:
            gl.drawText('Paint: OFF', 5, 110, 13)

        if finishTime:
            gl.drawText(f'Level completed in {round(finishTime,3)} seconds.', 5, 130, 13)
        else:
            gl.drawText(f'Timer: {round(t.time()-startTime,3) if startTime else 0}', 5, 130, 13)

        if help:
            if editor:
                gl.drawText(editorHelp, 5, 150, 15)
            else:
                gl.drawText(normalHelp, 5, 150, 15)

        if debug:
            gl.drawText('--- Debug ---', 5, 150, 14)
            gl.drawText(f'X: {str(cx):<11} Y: {cy}', 5, 166, 14)
            gl.drawText(f'VX: {str(vel[0]):<10} VY: {vel[1]}', 5, 180, 14)
            gl.drawText(f'Jumps: {jumps}', 5, 196, 14)
            gl.drawText(f'Dashes: {dashes}', 5, 210, 14)
            gl.drawText(f'OnGround: {onGround}', 5, 226, 14)
            gl.drawText(f'PressedX: {pressedX}', 5, 244, 14)
            gl.drawText(f'PressedY: {pressedY}', 5, 260, 14)

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
                    if gl.modPressed('ctrl'):
                        col = sprite.texture[startPos[0]][startPos[1]]

                        gl.floodfill(sprite.texture, startPos, selectedCol, col)

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
    global cx, cy, pressedX, pressedY, jumps, dashes, flight, noclip
    global meta, objects, clipboard, help, paint, selectedCol, hide_gui
    global finishTime, parachute, vel, debug, editor, startTime, typing
    key = key['key']
    if typing:
        if key == gl.pygame.K_RETURN:
            typing = False
        return

    if not startTime and key in {gl.pygame.K_w,gl.pygame.K_a,gl.pygame.K_s,gl.pygame.K_d,gl.pygame.K_SPACE,gl.pygame.K_UP}:
        startTime = t.time()

    match key:
        case gl.pygame.K_w:
            if flight:
                cy += 1

            elif jumps:
                jumps -= 1
                vel[1] += jumpForce
                cy += vel[1]

        case gl.pygame.K_UP:
            if gl.pygame.key.get_mods(): return
            if jumps:
                jumps -= 1
                vel[1] += jumpForce
                cy += vel[1]

        case gl.pygame.K_s:
            if editor and gl.modPressed('ctrl'):
                Level('level.txt').save_level(meta, objects)
                toast('Saved.')

        case gl.pygame.K_SPACE:
            if not (dashes or flight): return

            dashes -= 1
            if pressedX:
                vel[0] += dashForce * pressedX
            else:
                vel[0] += dashForce * (int(vel[0] > 0)-0.5)*2

        case gl.pygame.K_d:
            if gl.modPressed('ctrl') and gl.modPressed('shift'):
                debug = not debug
                toast(f'Debug: {debug}')

        case gl.pygame.K_q:
            game.running = False

        case gl.pygame.K_f:
            flight = not flight
            toast(f'Flight: {flight}')

        case gl.pygame.K_n:
            noclip = not noclip
            toast(f'Noclip: {noclip}')

        case gl.pygame.K_e:
            editor = not editor
            toast(f'Editor: {editor}')
            if flight != editor:
                toast(f'Flight: {flight}')
            flight = editor

        case gl.pygame.K_l:
            if not gl.modPressed('ctrl'): return

            for sprite in objects:
                if sprite == player: continue
                game.sprites.remove(sprite)

            file_name = filedialog.askopenfilename(filetypes=['Level .lvl'],initialdir='levels')
            meta, newObjects = Level(file_name).load_level()

            startTime = None
            finishTime = None
            
            objects = []
            for object in newObjects:
                type,x,y,width,height,attr,texture = object
                x,y,width,height = int(x),int(y),int(width),int(height)

                attr = dict([(i.split('=')[0], convert_type(i.split('=')[1].replace('~',','))) for i in attr.split(',')])
                texture = convert_type(texture)

                if type == 'platform':
                    object = Platform((x,y),width,height,attr)
                    object.sprite.updateTexture(texture)
                elif type == 'text':
                    object = Text((x,y), attr['text'], attr['size'], attr['color'], attr['bold'], attr['italic'])

                print(x, y, width, height, attr)

            toast('Level loaded.')

        case gl.pygame.K_DELETE:
            if not editor: return
            mouse_pos = gl.pygame.mouse.get_pos()
            pos = (mouse_pos[0]//game.res-cx,mouse_pos[1]//game.res-cy)
            pos = round(pos[0]), round(pos[1])

            for sprite in objects:
                if sprite.collidepoint(pos):
                    game.sprites.remove(sprite)
                    objects.remove(sprite)
                    toast('[Editor] Object deleted.')
                    break

        case gl.pygame.K_c:
            if not editor:
                parachute = not parachute

            else:
                mouse_pos = gl.pygame.mouse.get_pos()
                pos = (mouse_pos[0]//game.res-cx,mouse_pos[1]//game.res-cy)
                pos = round(pos[0]), round(pos[1])

                for sprite in objects:
                    if sprite.collidepoint(pos):
                            if gl.modPressed('ctrl'):
                                clipboard = [sprite.pos[0]-pos[0], sprite.pos[1]-pos[1], sprite.width,sprite.height,sprite.object.attributes,sprite.texture]
                                toast('[Editor] Object copied.')

                            else:
                                setattr(sprite, 'physics', not getattr(sprite, 'physics', True))
                                sprite.object.attributes['physics'] = getattr(sprite, 'physics')
                                toast(f'[Editor] Object physics: {sprite.object.attributes['physics']}')
                            break

        case gl.pygame.K_v:
            if not editor: return
            mouse_pos = gl.pygame.mouse.get_pos()
            pos = (mouse_pos[0]//game.res-cx,mouse_pos[1]//game.res-cy)
            pos = round(pos[0]), round(pos[1])

            if gl.modPressed('ctrl') and clipboard:
                x,y,width,height,attributes,paint = clipboard
                object = Platform((pos[0]+x,pos[1]+y),width,height,attributes)
                object.sprite.updateTexture(paint)
                toast('[Editor] Object pasted.')

        case gl.pygame.K_h:
            help = not help

        case gl.pygame.K_p:
            if gl.modPressed('ctrl'):
                selectedCol = colorchooser.askcolor(selectedCol, title = "Select Color")[0]
            else:
                paint = not paint

        case gl.pygame.K_r:
            respawn()
            ### [Vars/Init]
            jumps = 0
            dashes = 0
            vel = [0,0]
            pressedX = 0
            pressedY = 0
            startTime = 0
            finishTime = 0

            ### [Vars/Flags]
            flight  = False
            noclip  = False
            editor  = False
            help    = False
            paint = False
            toast('State Reset.')

        case gl.pygame.K_t:
            if not editor: return
            
            mouse_pos = gl.pygame.mouse.get_pos()
            pos = (mouse_pos[0]//game.res-cx,mouse_pos[1]//game.res-cy)
            pos = round(pos[0]), round(pos[1])

            typing = True

            Text(pos,'', input=True)

        case gl.pygame.K_F1:
            hide_gui = not hide_gui
            if hide_gui:
                toast('GUI hidden.')
            else:
                toast('GUI shown.')

    updateCamera()

@game.on('keyUp')
def keyUp(key):
    global cx, cy, pressedX, pressedY, parachute, typing
    if typing: return

    key = key['key']
    if key == gl.pygame.K_c and parachute:
        parachute = False

# Run the game
game.run()


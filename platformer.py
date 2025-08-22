from tkinter import colorchooser, filedialog
from collections.abc import Callable
from levelLoader import Level
from ast import literal_eval
import pygame_textinput
import engine as gl
import time as t
import os

VERSION = 5

def convert_type(s):
    try:
        return literal_eval(s)
    except:
        return s

### [Screen()]
class Screen:
    LEVEL_SELECT = 0
    PLAY = 1

### [Vars/Physics]
jumpForce = 1.2
gBendAmount = 3
gAccelerationAmount = 5
cameraFollowDistance = 4.5
universalPrecision = 8
dashForce = 0.85
gravity = 0.035
acceleration = 20
max_speed = 1.8
air_resistance = 0.97
friction = 0.98
maxJumps = 2
maxDashes = 1
parachuteResistance = 0.98

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
screen      = Screen.LEVEL_SELECT
flight      = False
noclip      = False
editor      = False
help        = False
paint       = False
debug       = False
typing      = False
onGround    = False
hide_gui    = False

normalHelp = """--- Movement ---
w - Jump/Up
a - Left
s - Down
d - Right
space - Dash
c - Brake

--- General ---
q - Quit
f  - Fly
n - Noclip
e - Editor
h - Help
p - Paint
r - Reset
esc - Level Select"""

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
selectedObj = 0
clipboard = None
selectedCol = (0,255,0)


### [Vars/Level]
objects = []
triggers = []
levelMeta = {"name": "Unnamed", "description": "No description"}

# Initialize the game
game = gl.Game("Platformer", (800,600), res=8, max_fps=60)
game.id = 'platformer'
game.version = VERSION

cx,cy = 0,10

# Load Shaders
shaders = {
    "gradient": gl.loadShaderFile('shaders/internal','gradient.py', {
        "gl": gl,
        "colors": [(120, 40, 255), (200, 30, 100)],
        "angle": 90,  # Angle in degrees
    })
}

# Add a player sprite
player_texture = [
    [(255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0)],
    [(255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0)],
    [(255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0)],
    [(255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0)],
    [(255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0)],
    [(255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0)],
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

    def setPos(self, x, y):
        self.sprite.setPos(x,y)
        self.pos = x,y
        self.sprite.x = x
        self.sprite.y = y
        self.x = x
        self.y = y

### [Platform(Object)]
class Platform(Object):
    def __init__(self, pos, width, height=6, attributes=None, shader = None):
        if attributes is None:
            attributes = {"bounciness": 0.5, "physics": True, "friction": friction}

        super().__init__(ObjectType.platform, pos, width, height, attributes, shader)
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
        super().__init__(ObjectType.text, pos, *gl.textSize(text, size), self.attributes, None)
        self.sprite.text = self

        if self.input:
            self.textinput = pygame_textinput.TextInputManager()

            def scroll(event):
                y = int(event['y'])
                print(y)
                self.attributes['size'] += y
            self.scroll = scroll

            game.on('scroll')(self.scroll)

            if 'all' in game.events:
                game.events['all'].append(self.textinput.update)
            else:
                game.events['all'] = [self.textinput.update]

    def render(self):
        global typing
        size = gl.textSize(self.attributes['text'],self.attributes['size'])
        size = int(size[0])//game.res+2, int(size[1])//game.res+1
        self.width, self.height = size
        self.sprite.width, self.sprite.height = size
        self.sprite.object.width, self.sprite.object.height = size

        if self.input and not typing:
            print(self.textinput.value)
            self.attributes['text'] = self.textinput.value[:-1]
            game.events['all'].remove(self.textinput.update)
            game.events['scroll'].remove(self.scroll)
            del self.textinput
            del self.scroll
            self.input = False

        if self.input:
            self.attributes['text'] = f'{self.textinput.left}|{self.textinput.right}'

        gl.drawText(self.attributes['text'], self.sprite.x*game.res, self.sprite.y*game.res, self.attributes['size'], self.attributes['color'], self.attributes['bold'], self.attributes['italic'])

### [TriggerType()]
class TriggerType:
    def __init__(self, type:str, run:Callable, color=(255,0,0)):
        self.type = type
        self.run = run
        self.color = color

        triggerTypes.append(self)

        class Trigger(Object):
            def __init__(self, pos, width, height, attributes, activation = TriggerActivationType.manual, behavior = TriggerActivationBehavior.once):
                self.activation = activation
                self.behavior = behavior
                self.state = TriggerState.ready
                attributes['type'] = type
                attributes['activation'] = activation
                attributes['behavior'] = behavior
                super().__init__(type+2, pos, width, height, attributes, None)
                self.sprite.trigger = self
                triggers.append(self)

            def render(self):
                if not editor: return
                gl.pygame.draw.rect(game.disp, color, (self.sprite.x*game.res, self.sprite.y*game.res,self.width*game.res,self.height*game.res))

            def run(self):
                run(self)

            def check_run(self):
                match self.behavior:
                    case TriggerActivationBehavior.once:
                        if self.state == TriggerState.ready:
                            self.run()
                            self.behavior = TriggerActivationBehavior.never
                    case TriggerActivationBehavior.repeat:
                        if self.state == TriggerState.ready:
                            self.run()
                    case TriggerActivationBehavior.continuous:
                        self.run
                    case TriggerActivationBehavior.never:
                        return

            def check(self):
                match self.activation:
                    case TriggerActivationType.vertical:
                        if self.x < player.x-cx+player.width/2 < self.x+self.width:
                            self.check_run()
                            self.state = TriggerState.triggered
                        else:
                            self.state = TriggerState.ready

                    case TriggerActivationType.horizontal:
                        if self.y < player.y-cy < self.y+self.height:
                            self.check_run()
                            self.state = TriggerState.triggered
                        else:
                            self.state = TriggerState.ready

                    case TriggerActivationType.touch:
                        testRect = gl.pygame.Rect(self.x,self.y,self.width,self.height)
                        playerRect = gl.pygame.Rect(player.x-cx,player.y-cy,player.width,player.height)

                        if testRect.colliderect(playerRect):
                            self.check_run()
                            self.state = TriggerState.triggered
                        else:
                            self.state = TriggerState.ready

        self.Trigger = Trigger

    def create(self, *args, **kwargs):
        return self.Trigger(*args, **kwargs)

triggerTypes = []

### [Enums]
class ObjectType:
    platform = 0
    text = 1
    trigger = 2

class TriggerActivationType:
    vertical = 0
    horizontal = 1
    touch = 2
    manual = 3

class TriggerActivationBehavior:
    once = 0
    repeat = 1
    continuous = 2
    never = 3

class TriggerState:
    ready = 0
    triggered = 1

class TriggerTypes:
    move = 0
    spawn = 1

def trigger(type, color):
    def decorator(func):
        TriggerType(type, func, color)
    return decorator

# Define trigger types

@trigger(TriggerTypes.move, (254, 46, 254))
def moveTrigger(self):
    for targetId in self.attributes['targets']:
        target = objects[targetId].object
        target.setPos(target.x+self.attributes['dx'],target.y+self.attributes['dy'])

@trigger(TriggerTypes.spawn, (0, 255, 255))
def spawnTrigger(self):
    for targetId in self.attributes['targets']:
        target = objects[targetId].trigger
        target.run()

### [Utils]
def respawn():
    global cx,cy,vel,startTime
    cy = 10
    cx = 0
    vel = [0,0]
    startTime = None

def updateCamera():
    global cx,cy,vel,startTime
    if cy <= -100:
        respawn()
        toast('You died.')

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

def load_level(path):
    global levelMeta, objects, triggers, startTime, finishTime
    for sprite in objects:
        if sprite == player: continue
        game.sprites.remove(sprite)

    levelMeta, newObjects = Level(path, VERSION).load_level()

    startTime = None
    finishTime = None

    objects = []
    triggers = []
    for object in newObjects:
        type,x,y,width,height,attr,*texture = object
        if texture: texture = texture[0]
        type,x,y,width,height = int(type),float(x),float(y),int(width),int(height)

        attr = dict([(i.split('=')[0], convert_type(i.split('=')[1].replace('~',','))) for i in attr.split(',')])
        texture = convert_type(texture)

        match type:
            case ObjectType.platform:
                object = Platform((x,y),width,height,attr)
                object.sprite.setPos(x,y)
                object.sprite.updateTexture(texture)

            case ObjectType.text:
                object = Text((x,y), attr['text'], attr['size'], attr['color'], attr['bold'], attr['italic'])

            case ObjectType.trigger:
                object = triggerTypes[attr['type']].create((x,y),width,height,attr,attr['activation'],attr['behavior'])

### [GameLoop/Event]
@game.on('frame')
def frame(frame):  # sourcery skip: low-code-quality
    # UI Screens
    if screen == Screen.LEVEL_SELECT:
        player.hidden = True
        draw_level_select()

    elif screen == Screen.PLAY:
        player.hidden = False
        physics()
        if not hide_gui:
            draw_gui()
        return

    player.hidden = True

def physics():
    global cx,cy, pressedX, jumps, dashes, finishTime, startTime, onGround
    ### [GameLoop/Apply velocity]
    vel[0] = vel[0] * (parachuteResistance if parachute else air_resistance)
    vel[1] = vel[1] * (parachuteResistance if parachute else air_resistance)

    cx += vel[0]
    cy += vel[1]

    ## [GameLoop/Check movement]
    pressedX = 0
    pressedY = 0
    if not (gl.modPressed('shift') or gl.modPressed('ctrl') or typing):
        if gl.keyPressed('w'):
            pressedY += 1
        if gl.keyPressed('a'):
            pressedX += 1
        if gl.keyPressed('s'):
            pressedY -= 1
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
            if object.type != ObjectType.platform:
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

    for trigger in triggers:
        trigger.check()

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

def draw_gui():
    # GUI
    gl.drawText(levelMeta['name'], 5, 5, 20)
    gl.drawText(levelMeta['description'], 10, 30, 12)

    modeText = f'Mode: {'Editor - ' if editor else ""}{mode or "None"}'
    gl.drawText(modeText, 5, 50, 13)

    gl.drawText(f'Noclip: {"ON" if noclip else "OFF"}', 5, 70, 13)
    gl.drawText(f'Flight: {"ON" if flight else "OFF"}', 5, 90, 13)
    gl.drawText(f'Paint: {"ON" if paint else "OFF"}', 5, 110, 13)

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

    if editor:
        gl.drawRect((453,5,200,98),(50,50,50),0,10)
        gl.drawText('--- Objects ---', 475, 5, 18)

        # Draw the grid
        for y in range(2):
            for x in range(4):
                gl.drawRect((460+x*35,30+y*35,30,30),(100,100,100),0,3)

        # Platform
        gl.drawRect((465,45,20,10),(255,255,255))

        # Text
        gl.drawText('T', 501, 27, 30)

        # Triggers

        # Move
        gl.drawRect((533,33,24,24),triggerTypes[TriggerTypes.move].color,0,3)

        # Spawn
        gl.drawRect((568,33,24,24),triggerTypes[TriggerTypes.spawn].color,0,3)

def scan_levels():
    """Scan the levels directory and load all available levels"""
    global levels
    levels = []

    # Check if levels directory exists
    if not os.path.exists('levels'):
        return

    # Get all .lvl files
    level_files = [f for f in os.listdir('levels') if f.endswith('.lvl')]

    # Load each level metadata
    for i, level_file in enumerate(level_files):
        try:
            path = os.path.join('levels', level_file)
            level_loader = Level(path, VERSION)
            meta, _ = level_loader.load_level()            # Create a LevelItem with adjusted dimensions
            list_x = game.width - 33  # Position in the right panel
            level_item = LevelItem(
                meta['name'],
                meta['description'],
                path,
                list_x,
                10 + (i * 20),  # Vertical spacing between items
                30,  # Width that fits in the panel
                15,  # Height for each item
                selected=(i == 0)  # Select first level by default
            )
            levels.append(level_item)

            # Set the first level as selected
            if i == 0:
                global selected_level
                selected_level = level_item

        except Exception as e:
            print(f"Error loading level {level_file}: {e}")

def draw_level_select():
    """Draw the level selection screen"""
    global levels, selected_level, level_scroll

    # First time init
    if not levels:
        scan_levels()

    game.backgroundShaders = [shaders["gradient"]]

    # Draw level list area background
    list_x = game.width - 33
    list_width = 32
    gl.drawRect((list_x*game.res, 5*game.res, list_width*game.res, (game.height-10)*game.res), (40, 40, 50), 0, 5)    # Draw visible levels
    visible_start = max(0, min(level_scroll, len(levels) - max_visible_levels))
    visible_end = min(len(levels), visible_start + max_visible_levels)

    for i, level in enumerate(levels[visible_start:visible_end]):
        level.x = list_x + 1  # Position levels in the list area
        level.y = 10 + (i * 22)  # Update position based on scroll, with more spacing between items
        level.width = list_width - 2  # Fit within list area
        level.height = 15  # Reasonable height for a list item
        level.draw()

    # Draw scroll indicators if needed
    if level_scroll > 0:
        gl.drawText("▲", (game.width - 18)*game.res, 3*game.res, 16)

    if visible_end < len(levels):
        gl.drawText("▼", (game.width - 18)*game.res, (game.height - 10)*game.res, 16)

    # Draw level details panel if a level is selected
    if selected_level:
        # Draw details panel background - make it smaller with spacing
        gl.drawRect((5,5,200,game.height*game.res-10), (60, 60, 70), 0, 5)

        # Draw level name and description with proper spacing
        gl.drawText(selected_level.name, 20*game.res, 20*game.res, 20)

        # Wrap description text
        desc = selected_level.description
        max_chars = 25  # Adjusted for smaller panel width
        wrapped_lines = [desc[i:i+max_chars] for i in range(0, len(desc), max_chars)]

        for i, line in enumerate(wrapped_lines):
            gl.drawText(line, 10*game.res, (25 + i * 5)*game.res, 14)

        # Draw play button
        play_btn_color = (100, 200, 100)
        mouse_pos = gl.pygame.mouse.get_pos()
        
        btn_x = game.width - 25
        btn_y = game.height - 15
        btn_width = 20
        btn_height = 10
        
        play_btn_rect = (btn_x*game.res, btn_y*game.res, btn_width*game.res, btn_height*game.res)

        # Check if mouse is over play button
        play_btn_hover = (
            play_btn_rect[0] <= mouse_pos[0] <= play_btn_rect[0] + play_btn_rect[2] and
            play_btn_rect[1] <= mouse_pos[1] <= play_btn_rect[1] + play_btn_rect[3]
        )

        if play_btn_hover:
            play_btn_color = (120, 220, 120)

        gl.drawRect(play_btn_rect, play_btn_color, 0, 5)
        gl.drawText("PLAY", (btn_x+5)*game.res, (btn_y+3)*game.res, 14)

### [LevelItem(Object)]
class LevelItem:
    def __init__(self, name, description, path, x, y, width=30, height=15, selected=False):
        self.name = name
        self.description = description
        self.path = path
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.selected = selected
        self.hover = False

    def draw(self):
        # Draw background rectangle with different colors for hover/selected states
        color = (150, 150, 200) if self.selected else (100, 100, 100)
        if self.hover and not self.selected:
            color = (120, 120, 120)

        gl.drawRect((self.x*game.res, self.y*game.res, self.width*game.res, self.height*game.res), color, 0, 5)

        # Draw level name and truncated description        gl.drawText(self.name, (self.x + 1)*game.res, (self.y + 1)*game.res, 14)
        desc_truncated = self.description[:20] + "..." if len(self.description) > 20 else self.description
        gl.drawText(desc_truncated, (self.x + 1)*game.res, (self.y + 6)*game.res, 10)
        
    def contains_point(self, pos):
        # Debug print to help diagnose click issues
        #print(f"Click at {pos}, button at {self.x},{self.y} with size {self.width}x{self.height}")
        return (self.x <= pos[0] <= self.x + self.width and
                self.y <= pos[1] <= self.y + self.height)

### [Vars/Level Select]
levels = []
selected_level = None
level_scroll = 0
max_visible_levels = 5
level_details_visible = False

### [Editor Mouse]
@game.on('mouseDown')
def mouseDown(event):  # sourcery skip: low-code-quality
    global startPos, grabPos, editedObj, editor, mode, selectedCol, oldTexture
    global selectedObj, typing
    if not editor: return
    pos = (event['pos'][0]//game.res-cx, event['pos'][1]//game.res-cy)
    pos = round(pos[0]), round(pos[1])

    # Object selector
    if event['pos'][0] in range(453,1000) and event['pos'][1] in range(5,93):
        pos = event['pos']
        selectedObj = (pos[0]-460)//35 + max(0,(pos[1]-30)//35*4)
        return

    # Left
    if event['button'] == 1:
        if paint:
            if not selectedCol: return
            for sprite in objects:
                if sprite.object.type != ObjectType.platform: return
                if sprite.collidepoint(pos):
                    startPos = pos[0]-sprite.pos[0], pos[1]-sprite.pos[1]

                    # Floodfill mode
                    if gl.modPressed('ctrl'):
                        col = sprite.texture[startPos[0]][startPos[1]]

                        gl.floodfill(sprite.texture, startPos, selectedCol, col)

                    # Pixel mode
                    else:
                        sprite.texture[startPos[0]][startPos[1]] = selectedCol
                    break
            return

        if not selectedObj:
            selectedObj = ObjectType.platform

        match selectedObj:
            case ObjectType.platform:
                startPos = pos
                mode = 'add'
                editedObj = Platform(pos,1,1)
                print('added')

            case ObjectType.text:
                typing = True
                editedObj = Text(pos,'', 30, input=True)

            case _:
                startPos = pos
                mode = 'add'
                editedObj = triggerTypes[selectedObj-2].create(
                    pos,
                    1,
                    1,
                    {
                        'dx': 0,
                        'dy': 0,
                        'targets': [],
                        'physics': False
                    },
                    TriggerActivationType.touch,
                    TriggerActivationBehavior.repeat
                )

    # Middle
    elif event['button'] == 2:
       for sprite in objects:
            if sprite.collidepoint(pos):
                startPos = sprite.pos[0]+sprite.width-1, sprite.pos[1]+sprite.height-1
                grabPos = sprite.pos[0]-pos[0], sprite.pos[1]-pos[1]
                mode = 'edit'
                editedObj = sprite
                break

    # Right
    elif event['button'] == 3:
        for sprite in objects:
            if sprite.collidepoint(pos):
                if paint and editor:
                    if sprite.object.type != ObjectType.platform: return
                    startPos = pos[0]-sprite.pos[0], pos[1]-sprite.pos[1]
                    sprite.texture[startPos[0]][startPos[1]] = game.bg

                else:
                    startPos = pos
                    grabPos = sprite.pos[0]-pos[0], sprite.pos[1]-pos[1]
                    mode = 'move'
                    editedObj = sprite
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
            editedObj.sprite.width = max(width,1)
            editedObj.sprite.object.width = max(width,1)

            if height < 1:
                editedObj.setPos(editedObj.x, pos[1])
                height = startPos[1]-pos[1]

            editedObj.height = max(height,1)
            editedObj.sprite.height = max(height,1)
            editedObj.sprite.object.height = max(height,1)

            if editedObj.texture[0]:
                editedObj.sprite.updateTexture(editedObj.gen_texture())

        elif mode == 'edit':
            if editedObj.object.type == ObjectType.text:
                pos = gl.pygame.mouse.get_pos()
                size = pos[1] - editedObj.y*game.res
                editedObj.text.attributes['size'] = max(int(size),1)

            else:
                pos = int(pos[0]+grabPos[0]), int(pos[1]+grabPos[1])
                editedObj.setPos(*pos)
                width = startPos[0]-pos[0]
                height = startPos[1]-pos[1]
                editedObj.object.width = max(width,1)
                editedObj.object.height = max(height,1)
                editedObj.object.sprite.width = max(width,1)
                editedObj.object.sprite.height = max(height,1)

                if editedObj.texture[0]:
                    editedObj.updateTexture(editedObj.object.gen_texture())

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
    global levelMeta, objects, clipboard, help, paint, selectedCol, hide_gui
    global finishTime, parachute, vel, debug, editor, startTime, typing, screen
    global triggers
    key = key['key']

    if typing:
        if key == 27:
            typing = False
        return

    if not startTime and key in {gl.pygame.K_w,gl.pygame.K_a,gl.pygame.K_s,gl.pygame.K_d,gl.pygame.K_SPACE,gl.pygame.K_UP}:
        startTime = t.time()

    match key:
        case gl.pygame.K_ESCAPE:
            if screen == Screen.PLAY:
                screen = Screen.LEVEL_SELECT
                toast('Returned to level select')
                return

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
                Level('levels/level.lvl').save_level(levelMeta, objects)
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

            lvl_path = filedialog.askopenfilename(filetypes=['Level .lvl'],initialdir='levels')
            if not lvl_path:
                return

            load_level()

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

        case gl.pygame.K_F1:
            hide_gui = not hide_gui
            if hide_gui:
                toast('GUI hidden.')
            else:
                toast('GUI shown.')

        case gl.pygame.K_t:
            shader_path = filedialog.askdirectory(initialdir='shaders',mustexist=True,title='Select shader')

            if not shader_path: return

            meta, bg_shaders, sprite_shaders = gl.loadShaders(shader_path)

            for bg_shader, cache in bg_shaders:
                if isinstance(bg_shader, tuple):
                    print(f'{bg_shader[0]}: {bg_shader[1]}')
                    return

                if cache:
                    bg_shader = gl.cache()(bg_shader)
                game.backgroundShaders.append(bg_shader)

            for sprite_shader, cache in sprite_shaders:
                if isinstance(sprite_shader, tuple):
                    print(f'{sprite_shader[0]}: {sprite_shader[1]}')
                    return
                if cache:
                    sprite_shader = gl.cache()(sprite_shader)
                game.spriteShaders.append(sprite_shader)

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

@game.on('mouseDown')
def levelSelectMouseDown(event):
    global selected_level, screen, levels, levelMeta, objects, triggers, level_scroll
    
    if screen != Screen.LEVEL_SELECT or editor:
        return
        
    pos = (event['pos'][0] // game.res, event['pos'][1] // game.res)
    
    # Debug print
    print(f"Mouse click at {pos} (scaled from {event['pos']})")
    
    # Check if click is in level list area
    divider_x = game.width - 35
    if pos[0] > divider_x:
        # Handle level selection
        visible_start = max(0, min(level_scroll, len(levels) - max_visible_levels))
        visible_end = min(len(levels), visible_start + max_visible_levels)
        
        for i, level in enumerate(levels[visible_start:visible_end]):
            print(f"Level {i}: pos={level.x},{level.y} size={level.width}x{level.height}")
            if level.contains_point(pos):
                print(f"Selected level: {level.name}")
                # Deselect previous level
                if selected_level:
                    selected_level.selected = False
                    
                # Select new level
                level.selected = True
                selected_level = level
                return
    
    # Check if click is on play button
    btn_x = game.width - 25
    btn_y = game.height - 15
    btn_width = 20
    btn_height = 10
    
    if (btn_x <= pos[0] <= btn_x + btn_width and
        btn_y <= pos[1] <= btn_y + btn_height and
        selected_level):

        # Load selected level
        try:
            level_loader = Level(selected_level.path)
            levelMeta, newObjects = level_loader.load_level()

            # Reset game state
            for sprite in objects:
                if sprite == player:
                    continue
                game.sprites.remove(sprite)

            objects = []
            triggers = []

            # Reset variables
            global jumps, dashes, vel, pressedX, pressedY, startTime, finishTime, parachute
            jumps = 0
            dashes = 0
            vel = [0, 0]
            pressedX = 0
            pressedY = 0
            startTime = 0
            finishTime = 0
            parachute = False

            # Load level objects
            for object in newObjects:
                type, x, y, width, height, attr, *texture = object
                if texture:
                    texture = texture[0]
                type, x, y, width, height = int(type), float(x), float(y), int(width), int(height)

                attr = dict([(i.split('=')[0], convert_type(i.split('=')[1].replace('~', ','))) for i in attr.split(',')])
                texture = convert_type(texture)

                match type:
                    case ObjectType.platform:
                        object = Platform((x, y), width, height, attr)
                        object.sprite.setPos(x, y)
                        object.sprite.updateTexture(texture)

                    case ObjectType.text:
                        object = Text((x, y), attr['text'], attr['size'], attr['color'], attr['bold'], attr['italic'])

                    case ObjectType.trigger:
                        object = triggerTypes[attr['type']].create(
                            (x, y), width, height, attr, attr['activation'], attr['behavior']
                        )
              # Change screen to play mode
            screen = Screen.PLAY
            respawn()

        except Exception as e:
            toast(f"Error loading level: {e}")

@game.on('mouseMove')
def levelSelectMouseMove(event):
    global levels, level_scroll
    
    if screen != Screen.LEVEL_SELECT or editor:
        return
        
    pos = (event['pos'][0] // game.res, event['pos'][1] // game.res)
    
    # Update hover state for levels
    visible_start = max(0, min(level_scroll, len(levels) - max_visible_levels))
    visible_end = min(len(levels), visible_start + max_visible_levels)
    
    for level in levels[visible_start:visible_end]:
        level.hover = level.contains_point(pos)

@game.on('scroll')
def levelSelectScroll(event):
    global level_scroll, levels
    
    if screen != Screen.LEVEL_SELECT or editor:
        return
        
    # Check if mouse is over the level list
    pos = (event['pos'][0] // game.res, event['pos'][1] // game.res)
    divider_x = game.width - 35
    if pos[0] < divider_x:
        return
        
    # Scroll up/down
    scroll_direction = -1 if event['y'] > 0 else 1
    level_scroll += scroll_direction
    
    # Clamp scroll value
    max_scroll = max(0, len(levels) - max_visible_levels)
    level_scroll = max(0, min(level_scroll, max_scroll))


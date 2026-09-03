
# GameEngine

A simple game engine for general use

## Platformer

An actual platformer game with a level editor, level loader and shader loader

## Drop

Vertical 1d bullet hell game with editor.

The example level is really hard btw.

### How to play

Dodge all the objects and you complete the level.

#### Controls

- A / left: move left
- D / right: move right
- §: Quick retry
- esc: Pause menu

#### Objects

Objects have 6 different properties:

- X position: Where the objects is on the X axis
- Time: When the object will hit the player line
- Width: How wide the object is
- Height: How tall it is
- Speed: How fast it moves
- Move speed (mv_speed): Changes the players movement speed

mv_speed is added to the player's current speed when the object hits the speed change line.

Objects are colored based on speed. If an object has mv_speed,
it is instead colored in purple by the amount it changes the player's speed.

### Editor Controls

- Left click + drag: create object
- Right click + drag object: move object
- Middle click + drag object: resize object

- Ctrl/shift + drag: select objects
- Left click + drag object: Select objects
- Ctrl + click object: select object
- Shift + click object: add object to selection

- Scroll: move through time
- Shift + scroll: change object's player move speed modifier
- Control + scroll: change object's speed
- Alt + scroll: change grid size

- Ctrl + s: save
- Ctrl + Esc: back to level select
- Ctrl + z: undo
- Ctrl + shift + z: redo

- Delete: delete object
- Ctrl + shift + alt + delete: delete all objects


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

### Level format

Optional metadata lines start with `:`. Object lines are comma separated
`time,x,width,height,speed,move_speed`, where trailing values may be omitted.

```
:name Example level
:description A pretty hard level
:song song.ogg
:markers 12.5,30,47.25

0,45,5,5,1.4,-0.5
```

Songs are loaded from `src/drop/songs/`, so `:song` only holds the file name.

`user.json` holds the cleared levels plus `music_volume` and `audio_offset_ms`,
the sync trim in milliseconds between the song and the level.

### Editor Controls

- Left click + drag: create object
- Right click + drag object: move object
- Middle click + drag object: resize object

- Ctrl/shift + drag: select objects
- Left click + drag object: Select objects
- Ctrl + click object: select object
- Shift + click object: add object to selection

- Space: Play/pause
- Scroll: move through time
- Shift + scroll: change object's player move speed modifier
- Control + scroll: change object's speed
- Alt + scroll: change grid size

- Click the top bar: jump the song to that position
- Ctrl + m: add a marker at the mouse position
- Ctrl + shift + m: delete the marker nearest to the cursor
- [ / ]: nudge the audio offset (hold shift for 25 ms)

- Ctrl + s: save
- Ctrl + Esc: back to level select
- Ctrl + z: undo
- Ctrl + shift + z: redo

- Delete: delete object
- Ctrl + shift + alt + delete: delete all objects

The thin bar along the top is the song timeline. Its brightness at each column
comes from that point of the song, markers are the yellow ticks, and the red
cursor reaches slightly below the bar so it stays findable.

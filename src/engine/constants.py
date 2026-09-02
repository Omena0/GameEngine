from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .classes.game import Game

# Populated by Game.__init__ at runtime.
game: "Game" = cast("Game", None)

VERSION = 12

dt = 1

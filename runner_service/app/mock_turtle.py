"""Mock turtle module for runner_service.

Replaces stdlib ``turtle`` so student code can call turtle functions
without opening a GUI window. Each call emits a ``TURTLE:<cmd>:<arg>``
line to stdout which the client-side TurtleRenderer picks up.
"""

from __future__ import annotations

import sys


class _MockTurtle:
    """Drop-in replacement for a turtle.Turtle() instance."""

    def forward(self, distance: float = 0) -> None:
        print(f"TURTLE:forward:{distance}")

    fd = forward

    def backward(self, distance: float = 0) -> None:
        print(f"TURTLE:backward:{distance}")

    bk = back = backward

    def right(self, angle: float = 0) -> None:
        print(f"TURTLE:right:{angle}")

    rt = right

    def left(self, angle: float = 0) -> None:
        print(f"TURTLE:left:{angle}")

    lt = left

    def penup(self) -> None:
        print("TURTLE:penup:")

    pu = up = penup

    def pendown(self) -> None:
        print("TURTLE:pendown:")

    pd = down = pendown

    def color(self, c: str = "") -> None:
        print(f"TURTLE:color:{c}")

    pencolor = color

    def goto(self, x: float = 0, y: float = 0) -> None:
        print(f"TURTLE:goto:{x},{y}")

    setpos = setposition = goto

    # no-ops for common calls that have no visual on canvas
    def speed(self, *_args) -> None:
        pass

    def shape(self, *_args) -> None:
        pass

    def hideturtle(self) -> None:
        pass

    ht = hideturtle

    def showturtle(self) -> None:
        pass

    st = showturtle

    def begin_fill(self) -> None:
        pass

    def end_fill(self) -> None:
        pass

    def done(self) -> None:
        pass

    def exitonclick(self) -> None:
        pass


class _MockScreen:
    """No-op replacement for turtle.Screen()."""

    def setup(self, *_args, **_kwargs) -> None:
        pass

    def bgcolor(self, *_args) -> None:
        pass

    def title(self, *_args) -> None:
        pass

    def mainloop(self) -> None:
        pass

    def bye(self) -> None:
        pass

    def exitonclick(self) -> None:
        pass


# Module-level singleton so ``import turtle; turtle.forward(100)`` works.
_default = _MockTurtle()
_screen = _MockScreen()

# Mirror the module-level API of stdlib turtle
forward = _default.forward
fd = _default.fd
backward = _default.backward
bk = _default.bk
back = _default.back
right = _default.right
rt = _default.rt
left = _default.left
lt = _default.lt
penup = _default.penup
pu = _default.pu
up = _default.up
pendown = _default.pendown
pd = _default.pd
down = _default.down
color = _default.color
pencolor = _default.pencolor
goto = _default.goto
setpos = _default.setpos
setposition = _default.setposition
speed = _default.speed
shape = _default.shape
hideturtle = _default.hideturtle
ht = _default.ht
showturtle = _default.showturtle
st = _default.st
begin_fill = _default.begin_fill
end_fill = _default.end_fill
done = _default.done
exitonclick = _default.exitonclick


def Turtle() -> _MockTurtle:  # noqa: N802 — matches stdlib API
    return _MockTurtle()


def Screen() -> _MockScreen:  # noqa: N802
    return _screen


def install() -> None:
    """Insert mock_turtle into sys.modules so ``import turtle`` resolves here."""
    sys.modules["turtle"] = sys.modules[__name__]

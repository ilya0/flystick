import pygame.joystick


class Ch(object):
    """Implements channel mixing.

    Mix examples:

        Reverse:
            -stick.axis(0)

        Offset:
            stick.axis(0) - 0.1

        Weight:
            stick.axis(0) * 0.5

        Mixing:
            stick.axis(0) - stick.axis(1) * 0.5

        Trim:
            stick.axis(0) - Switch(..) * 0.5

        Reverse + offset + weight + trim:
            (-stick.axis(0) + 0.1) * 0.7 - Switch(..) * 0.5

    Also a shortcut to scale the output to range [0..1]
    instead of the normal [-1..1]:
        +stick.axis(0)
    """
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, evts):
        return self.fn(evts)

    def __neg__(self):
        return Ch(lambda evts: -self.fn(evts))

    def __add__(self, x):
        if isinstance(x, float):
            return Ch(lambda evts: self.fn(evts) + x)
        elif isinstance(x, Ch):
            return Ch(lambda evts: self.fn(evts) + x(evts))
        else:
            raise ValueError("Invalid argument %r" % (x,))

    def __sub__(self, x):
        if isinstance(x, float):
            return Ch(lambda evts: self.fn(evts) - x)
        elif isinstance(x, Ch):
            return Ch(lambda evts: self.fn(evts) - x(evts))
        else:
            raise ValueError("Invalid argument %r" % (x,))

    def __mul__(self, x):
        if isinstance(x, float):
            return Ch(lambda evts: self.fn(evts) * x)
        elif isinstance(x, Ch):
            return Ch(lambda evts: self.fn(evts) * x(evts))
        else:
            raise ValueError("Invalid argument %r" % (x,))

    def __pos__(self):
        return Ch(lambda evts: .5 + self.fn(evts) / 2)


class Joystick(object):
    def __init__(self, joy_id):
        pygame.joystick.init()
        self._joy = pygame.joystick.Joystick(joy_id)
        self._joy.init()

    def axis(self, axis):
        return Ch(lambda evts: self._joy.get_axis(axis))

    def button(self, button):
        return Ch(lambda evts: 1. if self._joy.get_button(button) else -1.)

    def hat_switch(self, hat, axis, **switch):
        def hat_values(hats):
            for evt in hats:
                if evt.joy == self._joy.get_id() \
                   and evt.hat == hat:
                    yield evt.value[axis]
        return Switch(source=lambda (clicks, hats): hat_values(hats),
                      **switch)


def Switch(source, steps, initial=None):
    if initial is None:
        initial = 0
    step = [initial]
    def ch(evts):
        for value in source(evts):
            if value > 0:
                step[0] = (step[0] + 1) % steps
            elif value < 0:
                step[0] -= 1
                if step[0] < 0:
                    step[0] += steps
            # ignore zero
        return 2. * step[0] / (steps - 1) - 1
    return Ch(ch)


def XDot(center):
    col, row = center

    def render(value, scrollphat):
        x = int(round(value * 2))
        scrollphat.set_pixel(col + x, row - 4, True)

    return render


def YDot(col):
    def render(value, scrollphat):
        y = 2 + int(round(value * 2))
        scrollphat.set_pixel(col, y - 4, True)

    return render


class XYDot(object):
    def __init__(self, col):
        self.col = col
        self.x = self.y = None

    def horizontal(self):
        def render(value, scrollphat):
            x = self.col + int(round(value * 2))
            if self.y is None:
                self.x = x
            else:
                scrollphat.set_pixel(x, self.y - 4, True)
                self.x = self.y = None
        return render

    def vertical(self):
        def render(value, scrollphat):
            y = 2 + int(round(value * 2))
            if self.x is None:
                self.y = y
            else:
                scrollphat.set_pixel(self.x, y - 4, True)
                self.x = self.y = None
        return render


def YBar(col, width=1):
    cols = [col + x for x in range(width)]
    bars = (
        0b00000,
        0b00001,
        0b00011,
        0b00111,
        0b01111,
        0b11111,
    )

    def render(value, scrollphat):
        height = int(round((value + 1) / 2 * 5))
        for col in cols:
            scrollphat.set_col(col, bars[height])

    return render


def Block(corner, size=(1, 1)):
    # unpack for readability
    col, row = corner
    width, height = size
    xs = [col + x for x in range(width)]
    ys = [row + y for y in range(height)]

    def render(value, scrollphat):
        if value >= 0:
            for x in xs:
                for y in ys:
                    scrollphat.set_pixel(x, y - 4, True)

    return render

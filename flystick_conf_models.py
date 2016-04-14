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

    def event(self, button=None, hat=None):
        if hat:
            hat, axis = hat
            def map_evts(hats):
                for evt in hats:
                    if evt.joy == self._joy.get_id() \
                       and evt.hat == hat:
                        yield evt.value[axis]
            return lambda (clicks, hats): map_evts(hats)
        elif button is not None:
            raise NotImplementedError
        else:
            raise ValueError("hat or button required")


def Switch(steps, source):
    step = [0]
    def ch(evts):
        for value in source(evts):
            if value > 0:
                step[0] = (step[0] + 1) % steps
            elif value < 0:
                step[0] -= 1
                if step[0] < 0:
                    step[0] += steps
        return 2. * step[0] / (steps - 1) - 1
    return Ch(ch)


def XDot(center):
    x, y = center

    def render(value, scrollphat):
        _x = x + int(round(value * 2))
        scrollphat.set_pixel(_x, 4 - y, True)

    return render


def YDot(center_x):
    def render(value, scrollphat):
        _y = 2 + int(round(value * 2))
        scrollphat.set_pixel(center_x, 4 - _y, True)

    return render


class XYDot(object):
    def __init__(self, center_x):
        self.center_x = center_x
        self.x = self.y = None

    def horizontal(self):
        def render(value, scrollphat):
            x = self.center_x + int(round(value * 2))
            if self.y is None:
                self.x = x
            else:
                scrollphat.set_pixel(x, 4 - self.y, True)
                self.x = self.y = None
        return render

    def vertical(self):
        def render(value, scrollphat):
            y = 2 + int(round(value * 2))
            if self.x is None:
                self.y = y
            else:
                scrollphat.set_pixel(self.x, 4 - y, True)
                self.x = self.y = None
        return render


def YBar(center_x, width=1):
    xs = [center_x + x for x in range(width)]

    def render(value, scrollphat):
        height = int(round((value + 1) / 2 * 5))
        # could be optimized by using ``scrollphat.set_col``, but
        # would be difficult to read
        for x in xs:
            for y in range(0, height):
                scrollphat.set_pixel(x, 4 - y, True)

    return render


def Block(corner, size=(1, 1)):
    # unpack for readability
    corner_x, corner_y = corner
    x_size, y_size = size
    xs = [corner_x + x for x in range(x_size)]
    ys = [corner_y + y for y in range(y_size)]

    def render(value, scrollphat):
        if value >= 0:
            for x in xs:
                for y in ys:
                    scrollphat.set_pixel(x, 4 - y, True)

    return render

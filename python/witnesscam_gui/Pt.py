import math


class Pt:
    def __init__(self, x, y):
        pp('init')
        self.x = x
        self.y = y

    def length(self):
        return self.length2()

    def length2(self):
        return self.x**2 + self.y**2

    def t(self):
        return (self.x, self.y)

    def __str__(self):
        pp('str')
        return 'Pt(' + str(self.x) + ", " + str(self.y) + ")"

    def __repr__(self):
        pp('repr')
        return str(self)

    def __call__(self):
        pp('call')
        return True

    def __eq__(self, other):
        pp('eq')
        if type(self) == type(other):
            return self.x == other.x and self.y == other.y
        else:
            return False

    def __ne__(self, other):
        pp('ne')
        return not (self == other)

    def __add__(self, other):
        pp('plus')
        if type(self) == type(other):
            return Pt(self.x + other.x, self.y + other.y)
        else:
            raise TypeError('Cannot add ' +
                            str(type(self)) + " to " + str(type(other)))

    def __neg__(self):
        return Pt(-self.x, -self.y)

    def __sub__(self, other):
        return self + (-other)


def pp(s):
    if False:
        print(s)

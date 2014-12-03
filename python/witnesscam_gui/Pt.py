# Custom point class with mathematical operators suppoer
#
# Technology for Nature. British Natural History Museum insect specimen
# digitization project.
#
# Copyright (C) 2014    Syed Zahir Bokhari, Prof. Michael Terry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

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

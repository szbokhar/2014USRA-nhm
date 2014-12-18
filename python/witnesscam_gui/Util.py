# Utility module
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

from Pt import *
from time import time
from PySide import QtTest, QtCore
import json
import os
import csv


def computeImageScaleFactor(original, box):
    """Compute the factor to scale the original image by so that it fits in the
    perfectly in the provided box without changing the original aspect ratio.

    Keywords Arguments:
    original -- the (width, height) of the original image
    box -- the (width, height) of the box to fit the image in

    Return: (width, height, factor)
    width -- the width of the scaled image
    height -- the height of the scaled image
    factor -- the factor that scales the original size to the new size
    """

    (bW, bH) = box
    (w, h) = original
    rat = min(float(bW)/w, float(bH)/h)
    return (int(w*rat), int(h*rat), rat)


def buildPolygonSquareModel(points):
    """Given the points of a quadrilateral, compute the coefficents necessary
    to map any point within the quadrilateral to an appropriate point on the
    unit square. This mapping is such that each of the corners of the
    quadrilateral uniquly map to each of the corners of the unit square.

    Keyword Arguments:
    points -- list of points Pt(x,y) of the polygon in clockwise order starting
        from the top-left

    Return: model
    model -- a tuple containing the individual coefficents"""

    [p0, p1, p2, p3] = points
    [p00, p01, p02, p03] = [p0-p0, p1-p0, p2-p0, p3-p0]

    C = 0
    F = 0
    den2 = float(((p2-p1).x*(p2-p3).y-(p2-p1).y*(p2-p3).x))
    numG = float(((p2-p0).x*(p2-p3).y-(p2-p0).y*(p2-p3).x))
    numH = float(((p2-p1).x*(p2-p0).y-(p2-p1).y*(p2-p0).x))
    GG = numG/den2
    HH = numH/den2
    A = GG*(p1-p0).x
    D = GG*(p1-p0).y
    B = HH*(p3-p0).x
    E = HH*(p3-p0).y
    G = GG-1
    H = HH-1

    return (p0, A, B, C, D, E, F, G, H)


def poly2square(model, scalex, scaley, pos):
    """Maps a point inside a quadrilateral to a unique point on a rectangle.
    This function is the inverse of square2poly(..)

    Keyword Arguments:
    model -- a polygon-square model produced by buildPolygonSquareModel(..)
    scalex -- the width of the rectangle that the point is getting mapped
    scaley -- the height of the rectangle that the point is getting mapped
    pos -- the point Pt(x,y) inside the polygon

    Return: point
    point -- the corresponding point inside the rectangle"""

    (p0, A, B, C, D, E, F, G, H) = model
    (x, y) = (pos.x-p0.x, pos.y-p0.y)

    v = (-A*F+A*y+C*D-C*G*y-D*x+F*G*x)/(A*E-A*H*y-B*D+B*G*y+D*H*x-E*G*x)
    u = (-C-B*v+x+H*v*x)/(A-G*x)

    return Pt(int(u*scalex), int(v*scaley))


def square2poly(model, scalex, scaley, pos):
    """Maps a point inside a rectangle to a unique point on a quadrilateral.
    This function is the inverse of poly2square(..)

    Keyword Arguments:
    model -- a polygon-square model produced by buildPolygonSquareModel(..)
    scalex -- the width of the rectangle that the point is located on
    scaley -- the height of the rectangle that the point is located on
    pos -- the point Pt(x,y) inside the polygon

    Return: point
    point -- the corresponding point on the quadrilateral"""

    (p0, A, B, C, D, E, F, G, H) = model
    (u, v) = (pos.x/float(scalex), pos.y/float(scaley))

    x = (A*u+B*v+C)/(G*u+H*v+1) + p0.x
    y = (D*u+E*v+F)/(G*u+H*v+1) + p0.y

    return Pt(int(x), int(y))


def quadrilateralArea(points):
    """Compute the area of a convex quadrilateral.

    Keyword Arguments:
    points -- a list of the four (x,y) point of the quadrilateral in clockwise
        or counter-clockwise order

    Return: area
    area -- a float representing the area of the quadrilateral"""

    [p0, p1, p2, p3] = points
    return triangleArea([p0, p1, p2]) + triangleArea([p2, p3, p0])


def triangleArea(points):
    """Compute the area of a triangle.

    Keyword Arguments:
    points -- a list of the four (x,y) point of the quadrilateral in clockwise
        or counter-clockwise order

    Return: area
    area -- a float representing the area of the quadrilateral"""

    [(x0, y0), (x1, y1), (x2, y2)] = points
    return abs(0.5*(x0*(y1-y2) + x1*(y2-y0) + x2*(y0-y1)))


def findWeightedMedianPoint2D(image, roi):
    """Finds the weighted median position in a 2D grayscale image within a
    specified region of interest.

    Keyword Arguments:
    image -- the 2D grayscale image
    roi -- the region of interest specified as a list of two points Pt(x,y),
        with the first being the top left, and the second being the bottom
        right of the region of interest

    Return: point
    point -- the point Pt(x,y) of the median of the grayscale intensity"""

    totalIntensity = 0.0
    xlist = []
    ylist = []
    area = (roi[1].x - roi[0].x)*(roi[1].y-roi[0].y)
    step = int(math.sqrt(area)/50)
    for x in range(roi[0].x, roi[1].x, step):
        for y in range(roi[0].y, roi[1].y, step):
            if image[y, x] > 0:
                totalIntensity += image[y, x]
                xlist.append((x, image[y, x]))
                ylist.append((y, image[y, x]))

    if xlist and ylist:
        return Pt(weightedMedian1D(xlist), weightedMedian1D(ylist))

    return None


def weightedMedian1D(lst):
    """Finds the median position/50th percentile of the elements in the list.

    Keyword Arguments:
    lst -- the list of values (i, mag) where 'i' is the cooridinate and 'mag'
        is the weight at that coordinate

    Return: pos
    pos -- the coordinate in the list where the median is located"""

    lst.sort()

    # Convert distribution of weights into cumulative distribution
    for i in range(1, len(lst)):
        (cord, weight) = lst[i]
        (_, prev_weight) = lst[i-1]
        lst[i] = (cord, weight+prev_weight)

    # Binary search for the mid value in the cumulative distribution
    if lst:
        xmed = lst[-1][1]/2
        low = 0
        high = len(lst)-1
        while (high-low > 1):
            check = int(math.floor((high+low)/2))
            (v, w) = lst[check]
            if w > xmed:
                high = check
            elif w < xmed:
                low = check
            else:
                low = check
                high = check
                break
        return lst[high][0]


def getOverlappingBox(boxes, box, threshold=0.5):
    """Determines whether the supplied box overlaps 'threshold'% of any of the
    boxes in the supplied list of boxes.

    Keyword Arguments:
    boxes -- list of boxes (x1,y1,x2,y2) where (x1,y1) is the top right, and
        (x2,y2) is the bottom left of the box
    box -- the box (x1,y1,x2,y2) that we are checking for overlap with
    threshold -- the percentage of overlap [0,1] to consider the test box
        overlapping

    Return: (index, percentage)
    index -- the first box in the 'boxes' list that overlaps the test box
         (-1 if no box overlaps)
    percentage -- the percentage of 'box' that overlaps the first overlapping
        box in 'boxes'"""

    (x1, y1, x2, y2) = box
    i = 0
    for b in boxes:
        (u1, v1, u2, v2) = b

        if not (x1 > u2 or u1 > x2 or y1 > v2 or v1 > y2):
            a = max(x1, u1)
            b = max(y1, v1)
            c = min(x2, u2)
            d = min(y2, v2)
            overlap_area = abs(a-c)*abs(b-d)
            total_area = (u2-u1)*(v2-v1)
            perc = overlap_area/float(total_area)

            # Only consider overlapping if more than 50% of the test box
            # overlaps this one
            if perc >= threshold:
                return i

        i += 1

    return -1


def pointInBox(p, box):
    """Determines whether a point lies inside an axis aligned box.

    Keyword Arguments:
    p -- the test point (x,y)
    box -- the box to check (x1,y1,x2,y2)

    Return: inBox
    inBox -- True if the point is in the box, False otherwise"""

    (x1, y1, x2, y2) = box
    (x, y) = p

    return x > x1 and x < x2 and y > y1 and y < y2


def dedup_list(seq, idfun=None):
    """Removes duplicates from a list, preserving the order of the first
    non-uniqe elements

    Keyword Arguments:
    seq -- list of elements
    idfun -- function that converts an element to a comparison space

    Return: result
    result -- the de-deuplicated list"""

    if idfun is None:
        def idfun(x):
            return x

    seen = {}
    result = []
    for i in seq:
        marker = idfun(i)
        if marker in seen:
            continue
        seen[marker] = 1
        result.append(i)
    return result


def changeExtension(fname, ext):
    """Change the extension of a filename represented as a string."""

    csvfile = fname.split('.')
    csvfile[1] = ext
    csvfile = '.'.join(csvfile)
    return csvfile


class BugBox:
    """This class holds the data for one insect and its corresponding point and
    box. The static box is where the insect is in the loaded image, while the
    live box is where the insect appears in the camera view"""

    def __init__(self, name, livebox, staticbox, pt):
        """Constructor

        Keyword Arguments:
        name -- Name/ID of the insect (string)
        livebox -- (x1,y1,x2,y1) ints representing the top left (x1,y1) and
            bottom right (x2,y2) of the insect box in the live camera view
        staticbox -- (x1,y1,x2,y2) ints for the box in the tray scan image
        pt -- (x,y) ints representing the position of the insect in the
            tray scan"""

        self.name = name
        self.live = livebox
        self.static = staticbox
        self.point = pt

    def __str__(self):
        """Convert BugBox to a string representation"""

        return "BugBox('" + self.name +\
            "', static=" + str(self.static) +\
            ", live=" + str(self.live) +\
            ", point=" + str(self.point) + ")"

    def __repr__(self):
        return str(self)

    def getStaticBox(self, scale=1):
        """Returns the static box with the convienece of a multiplier.

        Keyword Arguments:
        scale -- multiply box coordinates by this scalar before returning"""

        (x1, y1, x2, y2) = self.static
        return (int(x1*scale), int(y1*scale), int(x2*scale), int(y2*scale))

    def getPoint(self, scale=1):
        """Returns the static point with the convienece of a multiplier.

        Keyword Arguments:
        scale -- multiply point coordinates by this scalar before returning"""

        (x1, y1) = self.point
        return (int(x1*scale), int(y1*scale))

    def __eq__(s, o):
        """Equality test"""

        try:
            return s.name == o.name\
                and s.live == o.live\
                and s.static == o.static\
                and s.point == o.point
        except AttributeError:
            return False


class BugBoxList:
    """Class that manage a list of BugBox instances. While
    attributes of BugBox instances can be changed manually, modifying them
    with this class's functions will allow for easy undo/redo functionality"""

    class Action:
        """Class representing an action done on a BugBox that can be
        undone or redone"""

        # Undo-able actions
        CREATE_BOX, DELETE_BOX, TRANSFORM_BOX_FROM = range(3)

        def __init__(self, kind, index=None, box=None, name=None,
                     static=None, live=None, point=None):
            """Constructor. This should not be called directly. It is better
            to create actions using the static menthods newBox(..),
            deleteBox(..), and changeBox(..)"""

            self.ts = time()
            self.action = kind
            self.index = index
            self.box = box
            self.name = name
            self.static = static
            self.live = live
            self.point = point
            self.recomputeLiveBoxes = False

        @staticmethod
        def newBox(i):
            """Returns an action for creating a new box.

            Keyword Arguments:
            i -- position in the BugBoxList the new box was created at"""

            return BugBoxList.Action(BugBoxList.Action.CREATE_BOX, index=i)

        @staticmethod
        def deleteBox(index, box):
            """Returns an action for deleting a box.

            Keyword Arguments:
            b -- the actual BugBox instance that was removed form the list"""

            return BugBoxList.Action(BugBoxList.Action.DELETE_BOX, index=index,
                                     box=box)

        @staticmethod
        def changeBox(i, name=None, static=None, live=None, point=None):
            """Returns an action for changing a box.

            Keyword Arguments:
            i -- index in th eBugBuxList of the box that was changed
            name -- (string) the new name given to the box
            static -- (x1,y1,x2,y2) the new dimensions of the static box
            live -- (x1,y1,x2,y2) the new dimensions of the live box
            point -- (x,y) the new point for the box"""

            return BugBoxList.Action(
                BugBoxList.Action.TRANSFORM_BOX_FROM, index=i, name=name,
                static=static, live=live, point=point)

        def __str__(self):
            """Convert a BugBixList.Action to a string"""

            return str(self.ts) + " " + str(self.action)

        def __repr__(self):
            return str(self)

        def isSimilar(self, other):
            """Returns whether two actions are similar.
            This is meant to be used in the case when many actions are
            performed in quick succesion (such as resizing a box). Typically,
            similar actions should have the ability to be merged into one
            action.

            Keyword Arguments:
            other -- the other BugBixList.ACtion instance

            Return: bool"""

            return self.action is BugBoxList.Action.TRANSFORM_BOX_FROM\
                and other.action is BugBoxList.Action.TRANSFORM_BOX_FROM\
                and abs(self.ts - other.ts) < 1

        def merge(self, other):
            """Merge this action with the other action if they are similar"""

            if self.isSimilar(other):
                self.tx = other.ts
                return True
            else:
                return False

    def __init__(self):
        """Constructor"""

        self.boxes = []
        self.undoStack = []
        self.redoStack = []

    def newBox(self, box):
        """Add a new box to the list.

        Keyword Arguments:
        box -- BugBox instance that will be added to the list"""

        self.recordAction(BugBoxList.Action.newBox(len(self.boxes)),
                          self.undoStack)
        self.boxes.append(box)
        if box.live is None:
            self.recomputeLiveBoxes = True

    def shouldRecomputeLiveBoxes(self, i=None):
        """Returns whether a BugBox has an invalid livebox, or whether there is
        a BugBix in the BugBixList that has an invalid live box

        Keyword Arguments:
        i -- the index of the box to query. If left unspecified, then returns
            whether an invalid livebox exists in the list"""

        if i is None:
            return self.recomputeLiveBoxes
        elif i < len(self.boxes):
            return self.boxes[i].live is None

    def recomputedLiveBoxes(self):
        """Notifies that all invalid live boxes have been fixed"""

        self.recomputeLiveBoxes = False

    def __getitem__(self, index):
        """Allow array element access"""
        return self.boxes[index]

    def __iter__(self):
        """Iterator"""
        return iter(self.boxes)

    def __len__(self):
        """Returns the length of the list"""
        return len(self.boxes)

    def __str__(self):
        return str(self.boxes)

    def __repr__(self):
        return str(self)

    def getDict(self):
        box_dict = dict()
        for b in self.boxes:
            box_dict[b.name] = b
        return box_dict

    def delete(self, index):
        """Deletes the box at the index position from the list.

        Keyword Arguments:
        index -- position of the box in the list to delete"""

        box = self.boxes[index]
        self.recordAction(BugBoxList.Action.deleteBox(index, box),
                          self.undoStack)
        del self.boxes[index]

    def changeBox(self, index, name=None, live=None, static=None, point=None):
        """Change the box at the index position to have the new values
        specified
        Keyword Arguments:
        index -- index in th eBugBuxList of the box that was changed
        name -- (string) the new name given to the box
        static -- (x1,y1,x2,y2) the new dimensions of the static box
        live -- (x1,y1,x2,y2) the new dimensions of the live box
        point -- (x,y) the new point for the box"""

        self.recordAction(BugBoxList.Action.changeBox(
            index,
            name=self.boxes[index].name if name is not None else None,
            static=self.boxes[index].static if static is not None else None,
            live=self.boxes[index].live if live is not None else None,
            point=self.boxes[index].point if point is not None else None),
            self.undoStack)

        if name is not None:
            self.boxes[index].name = name
        if live is not None:
            self.boxes[index].live = live
        if static is not None:
            self.boxes[index].static = static
        if point is not None:
            self.boxes[index].point = point

    def recordAction(self, action, stack, clear_redo=True, allow_merge=True):
        """Logs that an action has taken place, and merges with the most
        recent action if possible.

        Keyword Arguments:
        action -- the BugBoxList.Action instance
        stack -- the action stack to record the action in
        clear_redo -- whether the redo stack should be cleared
        allow_merge -- whether it should be possible to merge this action with
            the one on the top of the stack"""

        if len(stack) == 0 or not allow_merge or not stack[-1].merge(action):
            stack.append(action)
            if clear_redo:
                self.redoStack = []

    def undoRedo(self, undo=True):
        """Undo an action or redo an action"""

        stack1 = self.undoStack
        stack2 = self.redoStack
        if not undo:
            stack1 = self.redoStack
            stack2 = self.undoStack

        act = None
        if len(stack1) > 0:
            act = stack1[-1]
            del stack1[-1]
        else:
            return None

        if act.action == BugBoxList.Action.CREATE_BOX:
            self.recordAction(BugBoxList.Action.deleteBox(
                act.index, self.boxes[act.index]), stack2, False, False)
            del self.boxes[act.index]
            return -1
        elif act.action == BugBoxList.Action.DELETE_BOX:
            self.recordAction(BugBoxList.Action.newBox(act.index),
                              stack2, False, False)
            self.boxes.insert(act.index, act.box)
            return act.index
        elif act.action == BugBoxList.Action.TRANSFORM_BOX_FROM:
            i = act.index
            box = self.boxes[i]
            self.recordAction(BugBoxList.Action.changeBox(
                i,
                name=box.name if act.name is not None else None,
                static=box.static if act.static is not None else None,
                live=box.live if act.live is not None else None,
                point=box.point if act.point is not None else None),
                stack2, False, False)
            box.name = act.name if act.name is not None else box.name
            box.static = act.static if act.static is not None else box.static
            box.live = act.live if act.live is not None else box.live
            box.point = act.point if act.point is not None else box.point
            return act.index if act.index is not None else -1

    def undo(self):
        return self.undoRedo(undo=True)

    def redo(self):
        return self.undoRedo(undo=False)

    def clearUndoRedoStacks(self):
        self.undoStack = []
        self.redoStack = []


class InteractionLogger:
    DEBUG, INTERACTION = range(2)

    def __init__(self, filename=None, logLevels=[0, 1]):
        self.filename = filename
        self.loggingFile = None
        self.startTime = time()
        self.logLevels = logLevels

    def start(self):
        if self.filename is not None:
            self.loggingFile = open(self.filename, 'w')

    def stop(self):
        self.log("EXIT logger")
        if self.loggingFile is not None:
            self.loggingFile.close()

    def log(self, string, level=0):
        if self.loggingFile is not None\
                and any(map(lambda x: x == level, self.logLevels)):
            self.loggingFile.write(
                str(time() - self.startTime) + " " + string + "\n")

class TestingData:
    @staticmethod
    def loadTestingFile(testfile):
        if testfile is not None:
            with open(testfile, 'r') as f:
                jd = json.loads(f.read())
                return TestingData(jd)
        else:
            return None

    def __init__(self, automate, cam, tray, csv, check, corners, calibration, rununtil):
        self.automate = automate
        self.camfile = cam
        self.trayfile = tray
        self.csvfile = csv
        self.checkcsvfile = check
        self.traycorners = corners
        self.calibration = calibration
        self.rununtil = rununtil

    def __init__(self, jd):
        self.automate = jd['automate']
        self.camfile = jd['camfile']
        self.trayfile = jd['trayfile']
        self.csvfile = jd['csvfile']
        self.checkcsvfile = jd['check-csvfile']
        self.traycorners = jd['traycorners']
        self.calibration = jd['calibration']
        self.rununtil = jd['rununtil']


    def setMainTestingWindow(self, win):
        self.window = win

    def runtest(self):
        w = self.window
        for [x,y] in self.traycorners:
            QtTest.QTest.mouseClick(
                w.lblBig, QtCore.Qt.LeftButton, pos=QtCore.QPoint(x,y),
                delay=100)

        QtTest.QTest.mouseClick(
            w.lblBig, QtCore.Qt.LeftButton, delay=self.rununtil)

        # w.data.exportToCSV(False)

        current_boxes = w.data.bugBoxList.getDict()
        check_boxes = self.loadCSVBoxes(self.checkcsvfile).getDict()

        eps = 0.05
        error = 0
        for n in current_boxes.iterkeys():
            (x1,y1,x2,y2) = current_boxes[n].static
            if n not in check_boxes.keys():
                print('No \'%s\' in verified list of boxes' % n)
                error += 1
            else:
                (u1,v1,u2,v2) = check_boxes[n].static
                w = abs(u2-u1)
                h = abs(v2-v1)

                if (abs(x1-u1) < w*eps and abs(x2-u2) < w*eps and
                        abs(y1-v1) < h*eps and abs(y2-v2) < h*eps):
                    print('\'%s\' matches' % n)
                else:
                    print('\'%s\' dont match' % n)
                    error += 1
        print('%d errors found in regression test' % error)

    def loadCSVBoxes(self, csv_fname):
        boxes = None
        if os.path.isfile(csv_fname):
            with open(csv_fname) as csvfile:
                reader = csv.reader(csvfile)
                boxes = BugBoxList()

                if (reader.next()[1] == " Rectangle x1"):
                    for b in reader:
                        box = BugBox(
                            b[0], None,
                            (int(b[1]), int(b[2]), int(b[3]), int(b[4])),
                            (int(b[5]), int(b[6])))
                        boxes.newBox(box)

        return boxes

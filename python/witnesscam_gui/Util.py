from Pt import *
from time import time


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
    return 0.5*(x0*(y1-y2) + x1*(y2-y0) + x2*(y0-y1))


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
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for i in seq:
        marker = idfun(i)
        if marker in seen: continue
        seen[marker] = 1
        result.append(i)
    return result

class BugBox:
    def __init__(self, name, livebox, staticbox, pt):
        self.name = name
        self.live = livebox
        self.static = staticbox
        self.point = pt

    def __str__(self):
        return "BugBox('" + self.name +\
            "', static=" + str(self.static) +\
            ", live=" + str(self.live) +\
            ", point=" + str(self.point) + ")"

    def __repr__(self):
        return str(self)

    def getStaticBox(self, scale=1):
        (x1, y1, x2, y2) = self.static
        return (int(x1*scale), int(y1*scale), int(x2*scale), int(y2*scale))

    def getPoint(self, scale=1):
        (x1, y1) = self.point
        return (int(x1*scale), int(y1*scale))

    def __eq__(s, o):
        try:
            return s.name == o.name and\
                   s.live == o.live and\
                   s.static == o.static and\
                   s.point == o.point
        except AttributeError:
            return False

class BugBoxList:

    class Action:
        # Undoable actions
        CREATE_BOX, DELETE_BOX, TRANSFORM_BOX_FROM = range(3)

        def __init__(self, kind, index=None, box=None, name=None, static=None, live=None, point=None):
            self.ts = time()
            self.action = kind
            self.index = index
            self.box = box
            self.name = name
            self.static = static
            self.live = live
            self.point = point

        @staticmethod
        def newBox(i):
            return BugBoxList.Action(BugBoxList.Action.CREATE_BOX, index=i)

        @staticmethod
        def deleteBox(index, box):
            return BugBoxList.Action(BugBoxList.Action.DELETE_BOX, index=index, box=box)

        @staticmethod
        def changeBox(i, name=None, static=None, live=None, point=None):
            return BugBoxList.Action(BugBoxList.Action.TRANSFORM_BOX_FROM,
                          index=i, name=name, static=static, live=live,
                          point=point)

        def __str__(self):
            return str(self.ts) + " " + str(self.action)

        def __repr__(self):
            return str(self)

        def isSimilar(self, other):
            return self.action is BugBoxList.Action.TRANSFORM_BOX_FROM and\
                   other.action is BugBoxList.Action.TRANSFORM_BOX_FROM and\
                   abs(self.ts - other.ts) < 1

        def merge(self, other):
            if self.isSimilar(other):
                self.tx = other.ts
                return True
            else:
                return False


    def __init__(self):
        self.boxes = []
        self.undoStack = []
        self.redoStack = []

    def newBox(self, box):
        self.recordAction(BugBoxList.Action.newBox(len(self.boxes)), self.undoStack)
        self.boxes.append(box)

    def __getitem__(self, index):
        return self.boxes[index]

    def __iter__(self):
        return iter(self.boxes)

    def __len__(self):
        return len(self.boxes)

    def delete(self, index):
        box = self.boxes[index]
        self.recordAction(BugBoxList.Action.deleteBox(index, box), self.undoStack)
        del self.boxes[index]

    def changeBox(self, index, name=None, live=None, static=None, point=None):
        self.recordAction(BugBoxList.Action.changeBox(
            index,
            name= self.boxes[index].name if name is not None else None,
            static= self.boxes[index].static if static is not None else None,
            live= self.boxes[index].live if live is not None else None,
            point= self.boxes[index].point if point is not None else None),
            self.undoStack)

        if name is not None:
            self.boxes[index].name = name
        if live is not None:
            self.boxes[index].live = live
        if static is not None:
            self.boxes[index].static = static
        if point is not None:
            self.boxes[index].point = point


    def recordAction(self, action, stack, clearRedo=True, allowMerge=True):
        if len(stack) == 0 or not allowMerge or not stack[-1].merge(action):
            stack.append(action)
            if clearRedo:
                self.redoStack = []

    def undoRedo(self, undo=True):
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
            self.recordAction(BugBoxList.Action.deleteBox(act.index, self.boxes[act.index]), stack2, False, False)
            del self.boxes[act.index]
            return -1
        elif act.action == BugBoxList.Action.DELETE_BOX:
            self.recordAction(BugBoxList.Action.newBox(act.index), stack2, False, False)
            self.boxes.insert(act.index, act.box)
            return act.index
        elif act.action == BugBoxList.Action.TRANSFORM_BOX_FROM:
            i = act.index
            self.recordAction(BugBoxList.Action.changeBox(
                i,
                name= self.boxes[i].name if act.name is not None else None,
                static= self.boxes[i].static if act.static is not None else None,
                live= self.boxes[i].live if act.live is not None else None,
                point= self.boxes[i].point if act.point is not None else None),
                stack2, False, False)
            self.boxes[i].name = act.name if act.name is not None else self.boxes[i].name
            self.boxes[i].static = act.static if act.static is not None else self.boxes[i].static
            self.boxes[i].live = act.live if act.live is not None else self.boxes[i].live
            self.boxes[i].point = act.point if act.point is not None else self.boxes[i].point
            return act.index if act.index is not None else -1

    def undo(self):
        return self.undoRedo(undo=True)

    def redo(self):
        return self.undoRedo(undo=False)

    def clearUndoRedoStacks(self):
        self.undoStack = []
        self.redoStack = []

class InteractionLogger:
    def __init__(self, filename=None):
        self.filename = filename
        self.loggingFile = None
        self.startTime = time()

    def start(self):
        if self.filename is not None:
            self.loggingFile = open(self.filename, 'w')

    def stop(self):
        if self.loggingFile is not None:
            self.loggingFile.close()

    def log(self, string):
        if self.loggingFile is not None:
            self.loggingFile.write(str(time() - self.startTime) + " " + string + "\n")

from Pt import *

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

    return (p0,A,B,C,D,E,F,G,H)

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
    (p0,A,B,C,D,E,F,G,H) = model
    (x,y) = (pos.x-p0.x, pos.y-p0.y)

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
    (p0,A,B,C,D,E,F,G,H) = model
    (u,v) = (pos.x/float(scalex), pos.y/float(scaley))

    x = (A*u+B*v+C)/(G*u+H*v+1) + p0.x
    y = (D*u+E*v+F)/(G*u+H*v+1) + p0.y

    return Pt(int(x),int(y))

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
    for x in range(roi[0].x, roi[1].x, 5):
        for y in range(roi[0].y, roi[1].y, 5):
            if image[y,x] > 0:
                totalIntensity += image[y,x]
                xlist.append((x, image[y,x]))
                ylist.append((y, image[y,x]))

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
    for i in range(1,len(lst)):
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
    (x1,y1,x2,y2) = box
    i = 0
    for b in boxes:
        (u1,v1,u2,v2) = b

        if not (x1 > u2 or u1 > x2 or y1 > v2 or v1 > y2):
            a = max(x1,u1)
            b = max(y1,v1)
            c = min(x2,u2)
            d = min(y2,v2)
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
    (x1,y1,x2,y2) = box
    (x,y) = p

    return x > x1 and x < x2 and y > y1 and y < y2

class BugBox:
    def __init__(self, name, livebox, staticbox, pt):
        self.name = name
        self.live = livebox
        self.static = staticbox
        self.point = pt

    def __str__(self):
       return "BugBox('" + self.name + "', static=" + str(self.static) + ", live=" + str(self.live) + ")"

    def __repr__(self):
        return str(self)

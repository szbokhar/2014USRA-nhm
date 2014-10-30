from Pt import *

def keepAspectRatio(original, box):
    (bW, bH) = box
    (w, h) = original
    rat = min(float(bW)/w, float(bH)/h)
    return (int(w*rat), int(h*rat), rat)

def compute_polygon_model(points):
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
    (p0,A,B,C,D,E,F,G,H) = model
    (x,y) = (pos.x-p0.x, pos.y-p0.y)

    v = (-A*F+A*y+C*D-C*G*y-D*x+F*G*x)/(A*E-A*H*y-B*D+B*G*y+D*H*x-E*G*x)
    u = (-C-B*v+x+H*v*x)/(A-G*x)

    return (int(u*scalex), int(v*scaley))

def square2poly(model, scalex, scaley, pos):
    (p0,A,B,C,D,E,F,G,H) = model
    (u,v) = (pos.x/float(scalex), pos.y/float(scaley))

    x = (A*u+B*v+C)/(G*u+H*v+1) + p0.x
    y = (D*u+E*v+F)/(G*u+H*v+1) + p0.y

    return (int(x),int(y))

def area_of_quadrilateral(points):
    [p0, p1, p2, p3] = points
    return area_of_triangle([p0, p1, p2]) + area_of_triangle([p2, p3, p0])

def area_of_triangle(points):
    [(x0, y0), (x1, y1), (x2, y2)] = points
    return 0.5*(x0*(y1-y2) + x1*(y2-y0) + x2*(y0-y1))

def get_median_position(difference_mask, selection_boundingbox):
    c = 0.0
    p = Pt(0,0)
    xlist = []
    ylist = []
    for x in range(selection_boundingbox[0].x, selection_boundingbox[1].x, 5):
        for y in range(selection_boundingbox[0].y, selection_boundingbox[1].y,
                5):
            if difference_mask[y,x] > 0:
                c += difference_mask[y,x]
                xlist.append((x, difference_mask[y,x]))
                ylist.append((y, difference_mask[y,x]))
                p += Pt(x*difference_mask[y,x],y*difference_mask[y,x])

    if xlist:
        return Pt(median_pos(xlist), median_pos(ylist))

    return None

def median_pos(lst):
    lst.sort()
    for i in range(1,len(lst)):
        (cord, weight) = lst[i]
        (_, pweight) = lst[i-1]
        lst[i] = (cord, weight+pweight)

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

def getOverlappingBox(boxes, box):
    (x1,y1,x2,y2), _ = box
    i = 0
    for ((b, _), _) in boxes:
        (u1,v1,u2,v2) = b

        if not (x1 > u2 or u1 > x2 or y1 > v2 or v1 > y2):
            a = max(x1,u1)
            b = max(y1,v1)
            c = min(x2,u2)
            d = min(y2,v2)
            overlap_area = abs(a-c)*abs(b-d)
            total_area = (u2-u1)*(v2-v1)
            perc = overlap_area/float(total_area)

            if perc >= 0.8:
                return (i, boxes[i][0])

        i += 1

    return (-1, None)


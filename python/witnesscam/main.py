import numpy as np
import cv2
from Pt import *
from random import *
import math

corners = []
m_live = Pt(0,0)
m_static = Pt(0,0)
live_snap = None
box_range = None

def mouse_live(ev, x, y, flags, params):
    global corners
    global m_live
    if ev == 4 and len(corners) < 4:
        corners.append(Pt(x,y))
    m_live = Pt(x,y)

def mouse_static(ev, x, y, flags, params):
    global m_static
    m_static = Pt(x,y)

def amendImage(live_image, static_image, lp, sp):
    global corners
    global mapvals
    global live_snap

    if len(corners) < 4:
        for cl in corners:
            cv2.circle(live_image, (cl.x, cl.y), 8, (255,0,0))
        cv2.line(live_image, (lp.x-10, lp.y), (lp.x+10, lp.y), (0,255,0))
        cv2.line(live_image, (lp.x, lp.y-10), (lp.x, lp.y+10), (0,255,0))

    elif len(corners) == 4:
        """
        for i in [0,1,2,3]:
            p1 = corners[i]
            p2 = corners[(i+1)%4]
            cv2.line(live_image, (p1.x, p1.y), (p2.x, p2.y), (255, 0, 0))
        """
        l_height = live_image.shape[0]
        l_width = live_image.shape[1]
        (s_height, s_width, _) = static_image.shape
        mir = Pt(float(sp.x)/s_width, float(sp.y)/s_height)
        (u,v) = compute_mapvals(corners, s_width, s_height, lp)


        cv2.line(static_image, (u-10, v), (u+10, v), (0,255,0))
        cv2.line(static_image, (u, v-10), (u, v+10), (0,255,0))
        cv2.line(live_image, (lp.x-10, lp.y), (lp.x+10, lp.y), (0,255,0))
        cv2.line(live_image, (lp.x, lp.y-10), (lp.x, lp.y+10), (0,255,0))
        cv2.line(live_image, (lp.x-10, lp.y-10), (lp.x+10, lp.y+10), (255,255,255))
        cv2.line(live_image, (lp.x+10, lp.y-10), (lp.x-10, lp.y+10), (255,255,255))

def compute_mapvals(points, scalex, scaley, pos):
    [p0, p1, p2, p3] = points
    [p00, p01, p02, p03] = [p0-p0, p1-p0, p2-p0, p3-p0]
    (x,y) = (pos.x-p0.x, pos.y-p0.y)

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
    # den = G*u+H*v+1
    # x = (A*u+B*v+C)/den + p0.x
    # y = (D*u+E*v+F)/den + p0.y
    v = (-A*F+A*y+C*D-C*G*y-D*x+F*G*x)/(A*E-A*H*y-B*D+B*G*y+D*H*x-E*G*x)
    u = (-C-B*v+x+H*v*x)/(A-G*x)

    return (int(u*scalex), int(v*scaley))

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


cap = cv2.VideoCapture(0)
cv2.namedWindow('Live')
cv2.namedWindow('Static')
frame = None
cv2.setMouseCallback('Live', mouse_live)
cv2.setMouseCallback('Static', mouse_static)

static_image_base = cv2.imread('tray.png', cv2.IMREAD_COLOR)
static_image_base = cv2.pyrDown(static_image_base)
static_image_base = cv2.pyrDown(static_image_base)

while(True):
    # Capture frame-by-frame
    ret, big_frame = cap.read()
    small = cv2.pyrDown(big_frame)
    small = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)
    static_image = np.copy(static_image_base)
    small_blur = cv2.GaussianBlur(small, (13,13), 0)

    if live_snap == None:
        limg = small
        if len(corners) == 4:
            live_snap = cv2.GaussianBlur(small, (13,13), 0)
            (minx, miny, maxx, maxy) = (1000, 1000, 0, 0)
            for p in corners:
                minx = p.x if p.x < minx else minx
                miny = p.y if p.y < miny else miny
                maxx = p.x if p.x > maxx else maxx
                maxy = p.y if p.y > maxy else maxy
            box_range = [Pt(minx,miny), Pt(maxx, maxy)]
    else:
        limg = np.absolute(np.subtract(live_snap.astype(int), small_blur.astype(int))).astype(np.uint8)
        (h,w,d) = limg.shape
        mask = np.zeros((h,w,d), np.uint8)
        poly = np.array([[p.x, p.y] for p in corners], dtype=np.int32)
        cv2.drawContours(mask, [poly], 0, (1,1,1), -1)
        limg = np.float32(limg)
        limg = np.multiply(limg, mask)
        limg = np.square(limg)
        limg = np.add.reduce(limg, 2)
        limg = np.sqrt(limg)
        limg[limg < 12] = 0
        limg = limg/50

        xlist = []
        ylist = []
        for x in range(box_range[0].x, box_range[1].x, 10):
            for y in range(box_range[0].y, box_range[1].y, 10):
                if limg[y,x] > 0:
                    xlist.append((x, limg[y,x]))
                    ylist.append((y, limg[y,x]))

        if xlist:
            m_live = Pt(median_pos(xlist), median_pos(ylist))

    amendImage(limg, static_image, m_live, m_static)

    # Display the resulting frame
    cv2.imshow('Live',limg)
    cv2.imshow('Static',static_image)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('j'):
        live_snap = None

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()

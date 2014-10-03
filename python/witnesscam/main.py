import numpy as np
import cv2
import csv
from Pt import *
from random import *
import math

# Constants
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)

# Global variables
tray_corner_points = []
mouse_liveview = Pt(0,0)
mouse_staticview = Pt(0,0)
mouse_liveclick = 0
mouse_staticclick = 0
background_frame = None
selection_boundingbox = None

# Valid insect boxes loaded from CSV
csv_boxes = []
with open('butterfly_test.csv', 'rb') as csvfile:
    boxes =csv.reader(csvfile, delimiter=',')
    for b in boxes:
        if len(b) >= 5:
            csv_boxes.append([int(i) for i in b[1],b[2],b[3],b[4]])

# Callback for mouse events on the live view
def mouse_live(ev, x, y, flags, params):
    global tray_corner_points
    global mouse_liveview
    if ev == 4 and len(tray_corner_points) < 4:
        tray_corner_points.append(Pt(x,y))
    mouse_liveview = Pt(x,y)

# Callback form mouse events on the scanned view
def mouse_static(ev, x, y, flags, params):
    global mouse_staticview
    global mouse_staticclick
    mouse_staticview = Pt(x,y)
    if ev == 4:
        mouse_staticclick = 1

# Markup display image before displaying
def amendImage(live_image, static_image, lp, sp, pickbox, diff_center, static_target):
    global tray_corner_points
    global mapvals
    global background_frame
    global csv_boxes

    if len(tray_corner_points) < 4:
        for cl in tray_corner_points:
            cv2.circle(live_image, (cl.x, cl.y), 8, BLUE)
        cv2.line(live_image, (lp.x-10, lp.y), (lp.x+10, lp.y), GREEN)
        cv2.line(live_image, (lp.x, lp.y-10), (lp.x, lp.y+10), GREEN)

    elif len(tray_corner_points) == 4:
        cv2.line(live_image, (lp.x-10, lp.y), (lp.x+10, lp.y), GREEN)
        cv2.line(live_image, (lp.x, lp.y-10), (lp.x, lp.y+10), GREEN)
        cv2.line(live_image, (lp.x-10, lp.y-10), (lp.x+10, lp.y+10), WHITE)
        cv2.line(live_image, (lp.x+10, lp.y-10), (lp.x-10, lp.y+10), WHITE)

        (l_height, l_width) = live_image.shape
        (s_height, s_width, _) = static_image.shape
        if static_target != None:
            (u, v) = static_target
        elif diff_center != None:
            (u,v) = compute_mapvals(tray_corner_points, s_width, s_height,
                diff_center)
        else:
            (u,v) = (0,0)

        cv2.line(static_image, (u-10, v), (u+10, v), (0,255,0))
        cv2.line(static_image, (u, v-10), (u, v+10), (0,255,0))

        if pickbox:
            for b in csv_boxes:
                if (u > b[0] and u < b[2] and v > b[1] and v < b[3]):
                    q0 = (b[0], b[1])
                    q1 = (b[2], b[1])
                    q2 = (b[2], b[3])
                    q3 = (b[0], b[3])
                    cv2.line(static_image, q0, q1, (0,0,255))
                    cv2.line(static_image, q1, q2, (0,0,255))
                    cv2.line(static_image, q2, q3, (0,0,255))
                    cv2.line(static_image, q3, q0, (0,0,255))
                    break


# Compute mapping between quadrilateral and square
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
    v = (-A*F+A*y+C*D-C*G*y-D*x+F*G*x)/(A*E-A*H*y-B*D+B*G*y+D*H*x-E*G*x)
    u = (-C-B*v+x+H*v*x)/(A-G*x)

    return (int(u*scalex), int(v*scaley))

# Find the median of the list
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

# Find return all pixles with value 1 that are connected to the given pixel
def connected_component(img, pos):
    component = set()
    frontier = set([(pos.x, pos.y)])
    (h,w) = img.shape

    while frontier:
        (x,y) = frontier.pop()
        if x >= 0 and img[y, x-1] > 0 and (x-1,y) not in component:
            frontier.add((x-1,y))
        if x < w and img[y, x+1] > 0 and (x+1,y) not in component:
            frontier.add((x+1,y))
        if y >= 0 and img[y-1, x] > 0 and (x,y-1) not in component:
            frontier.add((x,y-1))
        if y < h and img[y+1, x] > 0 and (x,y+1) not in component:
            frontier.add((x,y+1))
        component.add((x,y))

    return component

def get_median_position(difference_mask, selection_bounding_box):
    c = 0.0
    p = Pt(0,0)
    xlist = []
    ylist = []
    for x in range(selection_boundingbox[0].x, selection_boundingbox[1].x, 10):
        for y in range(selection_boundingbox[0].y, selection_boundingbox[1].y,
                10):
            if difference_mask[y,x] > 0:
                c += difference_mask[y,x]
                xlist.append((x, difference_mask[y,x]))
                ylist.append((y, difference_mask[y,x]))
                p += Pt(x*difference_mask[y,x],y*difference_mask[y,x])

    if xlist:
        return Pt(median_pos(xlist), median_pos(ylist))

    return None

# Setup OpenCV stuff
cap = cv2.VideoCapture(0)
cv2.namedWindow('Live')
cv2.namedWindow('Static')
frame = None
cv2.setMouseCallback('Live', mouse_live)
cv2.setMouseCallback('Static', mouse_static)
static_image_base = cv2.imread('butterfy_test.png', cv2.IMREAD_COLOR)

# Scale down the csv box coordiantes for the loaded scanned image
(original_height, original_width, _) = static_image_base.shape
static_image_base = cv2.pyrDown(static_image_base)
static_image_base = cv2.pyrDown(static_image_base)
(h,w,_) = static_image_base.shape
scale = float(w)/original_width
for i in range(len(csv_boxes)):
    csv_boxes[i] = [int(c * scale) for c in csv_boxes[i]]


# Persistant values for the loop
last_dvalue = 0
current_dvalue = 0
stable_run = 0
static_target = None

while(True):
    # Capture frame-by-frame
    ret, big_frame = cap.read()
    small = cv2.pyrDown(big_frame)
    # small = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)
    static_image = np.copy(static_image_base)
    small_blur = cv2.GaussianBlur(small, (13,13), 0)
    difference_mask = small
    diff_center = None

    if background_frame == None:
        if len(tray_corner_points) == 4:
            background_frame = small_blur
            (minx, miny, maxx, maxy) = (1000, 1000, 0, 0)
            for p in tray_corner_points:
                minx = p.x if p.x < minx else minx
                miny = p.y if p.y < miny else miny
                maxx = p.x if p.x > maxx else maxx
                maxy = p.y if p.y > maxy else maxy
            selection_boundingbox = [Pt(minx,miny), Pt(maxx, maxy)]

    if background_frame != None:
        difference_mask = np.absolute(np.subtract(background_frame.astype(int),
                small_blur.astype(int))).astype(np.uint8)
        (h,w,d) = difference_mask.shape
        polygon_mask = np.zeros((h,w,d), np.uint8)
        poly = np.array([[p.x, p.y] for p in tray_corner_points],
                dtype=np.int32)
        cv2.drawContours(polygon_mask, [poly], 0, (1,1,1), -1)
        difference_mask = np.add.reduce(np.square(np.multiply(
                np.float32(difference_mask), polygon_mask)), 2)
        difference_mask = np.sqrt(difference_mask)
        difference_mask[difference_mask < 12] = 0
        difference_mask = difference_mask/50

        alp = 0.4
        current_dvalue = (1-alp)*last_dvalue + alp*math.sqrt(
                np.sum(difference_mask))

        print('A')
        if abs(current_dvalue-last_dvalue) < 5:
            print('B')
            stable_run += 1
        else:
            print('C')
            if static_target == None:
                print('D')
                stable_run = 0
            else:
                print('E')
                stable_run = -10
                static_target = (-1,-1)

        if stable_run == -1:
            print('E')
            background_frame = None
            stable_run = 0
            static_target = None

        diff_center = get_median_position(difference_mask,
                selection_boundingbox)

        if mouse_staticclick ==  1:
            background_frame = None
            mouse_staticclick = 0
            static_target = (mouse_staticview.x,mouse_staticview.y)
            current_dvalue = 0
        """
        if stable_run >= 5 and current_dvalue < 150:
            stable_run = 0
            background_frame = None
            """
        print(stable_run, static_target != None)

        last_dvalue = current_dvalue

    amendImage(difference_mask, static_image, mouse_liveview, mouse_staticview,
            abs(current_dvalue-last_dvalue) < 5, diff_center, static_target)

    # Display the resulting frame
    cv2.imshow('Live',difference_mask)
    cv2.imshow('Static',static_image)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('j'):
        background_frame = None

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()

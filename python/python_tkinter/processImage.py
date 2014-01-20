import cv2
import cv
from scipy import ndimage

win_width = 640
win_height = 480
phase = 0
back_pos = None
front_pos = None

# Draw ghost for mouse cursor
def click(x, y, data, phase):
    global back_pos
    global front_pos

    (main_image, ratio) = data
    sz = int(30*ratio)

    if phase < 2:
        # Draw rectangle on image
        if phase == 0:
            back_pos = (x,y)
        elif phase == 1:
            front_pos = (x,y)

    if phase == 1:
        seg_image = crop_image(main_image,
            scale_point(back_pos, 1/ratio),
            scale_point(front_pos, 1/ratio))
        return seg_image

    return None

# Resize image for display in window
def get_display_image(image):
    height, width, c = image.shape
    ratio = 1
    if height > win_height:
        ratio = win_height/float(height)
    elif width > win_width:
        ratio = win_width/float(width)

    return (cv2.resize(image, (int(width*ratio), int(height*ratio))), ratio)

def get_display_image_2D(image):
    height, width = image.shape
    ratio = 1
    if height > win_height:
        ratio = win_height/float(height)
    elif width > win_width:
        ratio = win_width/float(width)

    return (cv2.resize(image, (int(width*ratio), int(height*ratio))), ratio)


# scale a position by some amount
def scale_point((x,y), c):
    return (c*x, c*y)

# get the average grayscale color
def average(img):
    h,w = img.shape
    col = float(0)
    count = 0
    for y in range(h):
        for x in range(w):
            col += img[y,x]
            count+=1

    return col/float(count)

# Run the main crop routine based on user input
def crop_image(img, back, front):
    (bx,by) = back
    (fx,fy) = front

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 2)

    bcol = average(gray[(by-30):(by+30), (bx-30):(bx+30)])
    fcol = average(gray[(fy-30):(fy+30), (fx-30):(fx+30)])

    _, binary = cv2.threshold(gray, (bcol+fcol)/2, 255, cv2.THRESH_BINARY_INV)
    _, bin_lbl = cv2.threshold(gray, (bcol+fcol)/2, 1, cv2.THRESH_BINARY_INV)
    bin_show, _ = get_display_image_2D(binary)
    imlabel, lbl_count = ndimage.label(bin_lbl)

    return binary

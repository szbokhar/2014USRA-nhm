import cv2
import cv
import sys
from scipy import ndimage
import matplotlib.pyplot as plt

win_width = 800
win_height = 600
phase = 0
back_pos = None
front_pos = None

# Draw ghost for mouse cursor
def click(event, x, y, flags, data):
    global phase
    global back_pos
    global front_pos

    (main_image, img, ratio) = data
    sz = int(30*ratio)

    if event == cv2.EVENT_LBUTTONDOWN and phase < 2:
        cv2.rectangle(img, (x-sz,y-sz), (x+sz, y+sz), (0,0,0))
        cv2.imshow('showImage', img)

        if phase == 0:
            back_pos = (x,y)
        elif phase == 1:
            front_pos = (x,y)

        phase += 1
    elif phase < 2:
        imshow = img.copy()
        cv2.rectangle(imshow, (x-sz,y-sz), (x+sz, y+sz), (0,0,0))
        cv2.imshow('showImage', imshow)
    elif phase == 2:
        print "run segmentation"
        seg_image = crop_image(main_image,
            scale_point(back_pos, 1/ratio),
            scale_point(front_pos, 1/ratio))
        phase += 1

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
    print imlabel

    cv2.imshow('showImage', bin_show)
    plt.imshow(imlabel)
    plt.show()

# Main function
if __name__ == "__main__":
    fname = sys.argv[1]     # Get filename

    # Read image and generate display image
    cv2.namedWindow('showImage', cv2.WINDOW_NORMAL)
    main_image = cv2.imread(fname, 3)
    (display_image, ratio) = get_display_image(main_image)
    cv2.imshow('showImage', display_image)

    # Setup mouse callback and wait
    cv.SetMouseCallback('showImage', click, (main_image, display_image, ratio))
    cv2.waitKey(0)
    cv2.destroyAllWindows()


from PySide import QtCore, QtGui
import cv2
import csv
import numpy as np
import os.path
import sys

from Util import *
from Pt import *

BLUE = (255, 0, 0)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
CYAN = (255, 255, 0)


class AppData:
    """Main logic controler for the digitization gui"""

    # Hints
    HINT_LOADFILE = "Load a tray scan image by draggging a file here or using \
the file menu"
    HINT_TRAYAREA_1 = "Click on the top right corner of the tray in the scanned \
image in the live camera view."
    HINT_TRAYAREA_234 = "Now click on the next corner clockwise"
    HINT_REMOVEBUG_OR_EDIT = "Remove an insect from the tray and wait for it to be \
marked with a blue circle, or click a green marker to edit"
    HINT_REMOVEBUG = "Remove an insect from the tray and wait for it to be \
marked with a blue circle"
    HINT_ENTERBARCODE = "Scan the barcode for this insect"
    HINT_REPLACE_CONTINUE = "Once the barcode is entered correctly, replace the \
bug and remove the next one"
    HINT_EDITBOX = "Drag box to move. Scroll to resize. Click X to delete. \
Click another marker to edit it. Remove insect to continue with scanning"

    # Types of editing actions for boxes
    NO_ACTION, DG_NW, DG_N, DG_NE, DG_E, DG_SE, DG_S, DG_SW, DG_W, PAN = \
        range(10)

    # Number of stable frames to wait before performing certain actions
    DRAW_DELTA = 10
    CAM_MAX_WIDTH = 640
    CAM_MAX_HEIGHT = 480


    def __init__(self, win, cv_impl):
        """Initializes a bunch of member variables for use in later
        functions"""

        self.window = win
        self.implementation = cv_impl

        # Labels for displaying images
        self.controlPanel = None
        self.lblBig = None
        self.lblSmall = None

        # Filename
        self.trayPath = None
        self.trayImage = None
        self.csvPath = None

        # Whether the camera has been turned on yet
        self.camOn = False

        # Mouse cursors used when editing boxes
        self.resizeCursorH = QtGui.QCursor(QtCore.Qt.SizeHorCursor)
        self.resizeCursorV = QtGui.QCursor(QtCore.Qt.SizeVerCursor)
        self.resizeCursorB = QtGui.QCursor(QtCore.Qt.SizeBDiagCursor)
        self.resizeCursorF = QtGui.QCursor(QtCore.Qt.SizeFDiagCursor)
        self.prepanCursor = QtGui.QCursor(QtCore.Qt.OpenHandCursor)
        self.midpanCursor = QtGui.QCursor(QtCore.Qt.ClosedHandCursor)
        self.selectCursor = QtGui.QCursor(QtCore.Qt.CrossCursor)
        self.deleteCursor = QtGui.QCursor(QtCore.Qt.PointingHandCursor)
        self.normalCursor = QtGui.QCursor(QtCore.Qt.ArrowCursor)

        self.reset()

    def reset(self):
        # Mouse position (current and last) on the big label
        self.bigMPos = (0, 0)
        self.bigMLastPos = (0, 0)

        # Variables storing info about the quadrilateral containing the tray
        self.trayBoundingBox = None

        self.removedBug = -1

        # Variables used in keeping track of the placed boxes
        self.placedBoxes = []
        self.stableBoxRun = 0
        self.stableBox = None
        self.rescalePlacedboxes = False

        # Variables used for editing the boxes
        self.selectedEditBox = None
        self.editAction = AppData.NO_ACTION

        self.setHintText(AppData.HINT_LOADFILE)

    def setGuiElements(self, control, big, small):
        """Associate the elements of the gui with the application data.

        Keyword Arguments:
        control -- a ControlPanel instance
        big -- a BigLabel instance
        small -- a SmallLabel instance"""

        # Assign gui elements
        self.controlPanel = control
        self.lblBig = big
        self.lblSmall = small

        # Connect signals and slots
        self.lblBig.sigMousePress.connect(self.bigLabelMousePress)
        self.lblBig.sigMouseMove.connect(self.bigLabelMouseMove)
        self.lblBig.sigMouseRelease.connect(self.bigLabelMouseRelease)
        self.lblBig.sigScroll.connect(self.bigLabelScroll)

        self.setHintText(AppData.HINT_LOADFILE)

    def setTrayScan(self, image_fname, csv_fname):
        """Load the tray scan image and activate the camera.

        Keyword Arguments:
        image_fname -- the string filepath of the tray scan image"""

        # Export current csv if theer is one
        self.exportToCSV()

        # Clear data
        self.reset()

        # Load the image
        self.trayPath = image_fname
        self.trayImage = cv2.imread(self.trayPath, cv2.IMREAD_COLOR)
        self.csvPath = csv_fname

        # Load csv file
        if os.path.isfile(csv_fname):
            with open(csv_fname) as csvfile:
                reader = csv.reader(csvfile)
                self.placedBoxes = []
                if (reader.next()[1] == ' Rectangle x1'):
                    for b in reader:
                        box = BugBox(b[0], None, (int(b[1]), int(b[2]), int(b[3]),
                                     int(b[4])), (int(b[5]), int(b[6])))
                        self.placedBoxes.append(box)

                    self.window.statusBar().showMessage('Also loaded CSV file: ' + str(csv_fname.split('/')[-1]))
                else:
                    QtGui.QMessageBox.information(
                        self.window, 'Error Reading CSV',
                        'It seems the file ' + str(csv_fname.split('/')[-1]) +\
                        ' id badly formatted. Cannot load.')

        # Start the camera loop
        self.startCameraFeed()

        self.setHintText(AppData.HINT_TRAYAREA_1)

    def startCameraFeed(self):
        """Begin the camera feed and set up the timer loop."""

        if not self.camOn:
            self.capture = cv2.VideoCapture(0)

            self.frameTimer = QtCore.QTimer()
            self.frameTimer.timeout.connect(self.getNewCameraFrame)
            self.frameTimer.start(30)
            self.camOn = True

    def getNewCameraFrame(self):
        """This function is called by the timer 30 times a second to fetch a new
        frame from the camera, have it processed, and display the final result
        to on screen."""

        # Get new camera frame and reload fresh static frame
        _, self.cameraImage = self.capture.read()
        while (self.cameraImage.shape[0] > AppData.CAM_MAX_HEIGHT or
               self.cameraImage.shape[1] > AppData.CAM_MAX_WIDTH):
            self.cameraImage = cv2.pyrDown(self.cameraImage)

        # Process and modify the camera and static frames
        (big_image, small_image, self.placedBoxes) =\
            self.implementation.amendFrame(self.cameraImage, self.trayImage,
            self.lblBig.imageScaleRatio, self.lblSmall.imageScaleRatio,
            self.placedBoxes)

        if self.implementation.allowEditing():
            dB = int(AppData.DRAW_DELTA/self.lblBig.imageScaleRatio)
            self.draw_editing_ui(big_image, GREEN, RED, BLUE, dB)

        # Display the modified frame to the user
        self.lblBig.setImage(big_image)
        self.lblSmall.setImage(small_image)

    def setMousepos(self, x, y):
        """Update the current mouse position"""

        self.bigMPos = (x, y)

    def draw_editing_ui(self, image, regular, selected, active, a):
        """Given an input image, draw all of the generated boxes on the image.
        Optional colour paramaters can also be supplied.

        Keyword Arguments:
        image -- the numpy array image that the boxes will be drawn on
        regular -- the colour of the boxes
        selected -- the colour of the selected box
        """

        for i in range(len(self.placedBoxes)):

            b = self.placedBoxes[i].static
            (px, py) = self.placedBoxes[i].point
            t = max(int(a/5), 1)
            col = None

            if i == self.selectedEditBox:
                cv2.rectangle(image, b[0:2], b[2:4], selected, t)
                cv2.rectangle(image, (b[2]+a, b[1]-3*a), (b[2]+3*a, b[1]-a), selected, t)
                cv2.line(image, (b[2]+a, b[1]-3*a), (b[2]+3*a, b[1]-a), selected, t)
                cv2.line(image, (b[2]+3*a, b[1]-3*a), (b[2]+a, b[1]-a), selected, t)
                ((_,h),_) = cv2.getTextSize(self.placedBoxes[i].name, cv2.FONT_HERSHEY_SIMPLEX, a/18.0, t)
                cv2.putText(image, self.placedBoxes[i].name, (b[0]-int(a/2), b[3]+h), cv2.FONT_HERSHEY_SIMPLEX, a/18.0, WHITE, t)
                col = selected
            else:
                col = regular

            if i != self.removedBug:
                cv2.line(image, (px, py-a), (px, py+a), col, t)
                cv2.line(image, (px+a, py), (px-a, py), col, t)
                cv2.circle(image, (px, py), a, col, t)

    def refreshCameraButton(self):
        """When the refresh camer button is pressed"""
        self.implementation.refreshCamera()

    def exportToCSV(self):
        """Called when the Export to CSV button is pressed"""

        if self.csvPath == None or self.csvPath == "":
            return

        ret = QtGui.QMessageBox.Yes
        if os.path.isfile(self.csvPath):
            ret = QtGui.QMessageBox.question(
                self.window, 'Overwrite file',
                'File ' + str(self.csvPath.split('/')[-1]) + ' already exists. Would you like \
to overwrite it?', QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if ret == QtGui.QMessageBox.Yes:
            f = open(self.csvPath, 'w')
            f.write('Insect Id, Rectangle x1, y1, x2, y1, Point x, y\n')
            for b in self.placedBoxes:
                f.write(b.name + ", " +
                        str(b.getStaticBox())[1:-1] + ', ' +
                        str(b.getPoint())[1:-1] + '\n')
            self.window.statusBar().showMessage('Saved data to ' + str(self.csvPath.split('/')[-1]))

    def bigLabelMousePress(self, ev, scale):
        """When the mouse is clicked on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object
        scale -- scale constant between the size of the label and the size
            of the big label"""

        self.implementation.mousePress(ev, scale)

        if self.implementation.allowEditing():
            self.editMousePress(ev)

    def bigLabelMouseMove(self, ev, scale):
        """When the mouse is clicked on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object
        scale -- scale constant between the size of the label and the size
            of the big label"""
        self.setMousepos(int(ev.pos().x()/scale),
                         int(ev.pos().y()/scale))
        self.lblBig.setCursor(self.normalCursor)

        self.implementation.mouseMove(ev, scale)

        if self.implementation.allowEditing():
            self.editMouseMove()

    def bigLabelMouseRelease(self, ev, scale):
        """When the mouse is clicked on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object"""
        self.implementation.mouseRelease(ev, scale)
        if self.implementation.allowEditing():
            self.editMouseRelease()

    def bigLabelScroll(self, ev, scale):
        """When the mouse is clicked on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object"""
        self.implementation.mouseScroll(ev, scale)
        if self.implementation.allowEditing():
            self.editMouseScroll(ev)

    def editMousePress(self, ev):
        """Called when the application is in edit mode and the mouse is clicked
        on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object"""

        (mx, my) = self.bigMPos
        c = 15

        if self.selectedEditBox is not None:
            # If a box is selected, check for clicking on an editable point
            # (e. corners for resizing, center for panning)
            p = self.bigMPos
            (x1, y1, x2, y2) = self.placedBoxes[self.selectedEditBox].static
            a = int(AppData.DRAW_DELTA/self.lblBig.imageScaleRatio)
            if ev.button() == QtCore.Qt.MouseButton.LeftButton:
                # Process left click
                if pointInBox(p, (x1-c, y1-c, x1+c, y1+c)):
                    self.editAction = AppData.DG_NW
                elif pointInBox(p, (x2-c, y2-c, x2+c, y2+c)):
                    self.editAction = AppData.DG_SE
                elif pointInBox(p, (x1-c, y2-c, x1+c, y2+c)):
                    self.editAction = AppData.DG_SW
                elif pointInBox(p, (x2-c, y1-c, x2+c, y1+c)):
                    self.editAction = AppData.DG_NE
                elif pointInBox(p, (x1+c, y1-c, x2-c, y1+c)):
                    self.editAction = AppData.DG_N
                elif pointInBox(p, (x1+c, y2-c, x2-c, y2+c)):
                    self.editAction = AppData.DG_S
                elif pointInBox(p, (x1-c, y1+c, x1+c, y2-c)):
                    self.editAction = AppData.DG_W
                elif pointInBox(p, (x2-c, y1+c, x2+c, y2-c)):
                    self.editAction = AppData.DG_E
                elif pointInBox(p, (x1+c, y1+c, x2-c, y2-c)):
                    self.editAction = AppData.PAN
                elif pointInBox(p, (x2+a, y1-3*a, x2+3*a, y1-a)):
                    if self.removedBug == self.selectedEditBox:
                        self.implementation.refreshCamera()
                    del self.placedBoxes[self.selectedEditBox]
                    self.selectedEditBox = None

                    self.implementation.refreshCamera()

                if self.editAction != AppData.NO_ACTION:
                    return

        # If a box is not selected, check for clicking on a box to
        # to select it
        clickedOn = False
        for i in range(len(self.placedBoxes)):
            (x1, y1, x2, y2) = self.placedBoxes[i].static
            if pointInBox((mx, my), (x1-c, y1-c, x2+c, y2+c)):
                clickedOn = True
                self.selectedEditBox = i
                self.controlPanel.setCurrentBugId(self.placedBoxes[i].name)
                self.implementation.refreshCamera()
                self.implementation.setCurrentSelectionBox(self.placedBoxes, -1)
                self.setHintText(AppData.HINT_EDITBOX)

        # Check for deselect of box
        if not clickedOn:
            self.selectedEditBox = None
            self.setHintText(AppData.HINT_REMOVEBUG)

    def editMouseMove(self):
        """Called when the application is in edit mode and the mouse is moved
        on the big label."""

        p = self.bigMPos

        # Show box select cursor if hovered over box
        self.lblBig.setCursor(self.normalCursor)
        for b in self.placedBoxes:
            if pointInBox(p, b.static):
                self.lblBig.setCursor(self.selectCursor)

        # If box is selected, show various cursors for editing functions
        if self.selectedEditBox is not None:
            if self.editAction == AppData.NO_ACTION:
                c = 15
                a = int(AppData.DRAW_DELTA/self.lblBig.imageScaleRatio)
                (x1, y1, x2, y2) =\
                    self.placedBoxes[self.selectedEditBox].static
                if pointInBox(p, (x1-c, y1-c, x1+c, y1+c)):
                    self.lblBig.setCursor(self.resizeCursorF)
                elif pointInBox(p, (x2-c, y2-c, x2+c, y2+c)):
                    self.lblBig.setCursor(self.resizeCursorF)
                elif pointInBox(p, (x1-c, y2-c, x1+c, y2+c)):
                    self.lblBig.setCursor(self.resizeCursorB)
                elif pointInBox(p, (x2-c, y1-c, x2+c, y1+c)):
                    self.lblBig.setCursor(self.resizeCursorB)
                elif pointInBox(p, (x1+c, y1-c, x2-c, y1+c)):
                    self.lblBig.setCursor(self.resizeCursorV)
                elif pointInBox(p, (x1+c, y2-c, x2-c, y2+c)):
                    self.lblBig.setCursor(self.resizeCursorV)
                elif pointInBox(p, (x1-c, y1+c, x1+c, y2-c)):
                    self.lblBig.setCursor(self.resizeCursorH)
                elif pointInBox(p, (x2-c, y1+c, x2+c, y2-c)):
                    self.lblBig.setCursor(self.resizeCursorH)
                elif pointInBox(p, (x1+c, y1+c, x2-c, y2-c)):
                    self.lblBig.setCursor(self.prepanCursor)
                elif pointInBox(p, (x2+a, y1-3*a, x2+3*a, y1-a)):
                    self.lblBig.setCursor(self.deleteCursor)
            else:
                (dx, dy) = (self.bigMPos[0] - self.bigMLastPos[0],
                            self.bigMPos[1] - self.bigMLastPos[1])
                b = self.placedBoxes[self.selectedEditBox]
                (x1, y1, x2, y2) = b.static
                newBox = b.static
                (px, py) = b.point
                newPoint = b.point
                if self.editAction == AppData.DG_NW:
                    newBox = (x1+dx, y1+dy, x2, y2)
                    self.lblBig.setCursor(self.resizeCursorF)
                elif self.editAction == AppData.DG_N:
                    newBox = (x1, y1+dy, x2, y2)
                    self.lblBig.setCursor(self.resizeCursorV)
                elif self.editAction == AppData.DG_NE:
                    newBox = (x1, y1+dy, x2+dx, y2)
                    self.lblBig.setCursor(self.resizeCursorB)
                elif self.editAction == AppData.DG_E:
                    newBox = (x1, y1, x2+dx, y2)
                    self.lblBig.setCursor(self.resizeCursorH)
                elif self.editAction == AppData.DG_SE:
                    newBox = (x1, y1, x2+dx, y2+dy)
                    self.lblBig.setCursor(self.resizeCursorF)
                elif self.editAction == AppData.DG_S:
                    newBox = (x1, y1, x2, y2+dy)
                    self.lblBig.setCursor(self.resizeCursorV)
                elif self.editAction == AppData.DG_SW:
                    newBox = (x1+dx, y1, x2, y2+dy)
                    self.lblBig.setCursor(self.resizeCursorB)
                elif self.editAction == AppData.DG_W:
                    newBox = (x1+dx, y1, x2, y2)
                    self.lblBig.setCursor(self.resizeCursorH)
                elif self.editAction == AppData.PAN:
                    newBox = (x1+dx, y1+dy, x2+dx, y2+dy)
                    newPoint = (px + dx, py + dy)
                    self.lblBig.setCursor(self.midpanCursor)

                b.static = newBox
                b.point = newPoint

        self.bigMLastPos = self.bigMPos

    def editMouseRelease(self):
        """Called when the application is in edit mode and the mouse is released
        on the big label."""
        self.editAction = AppData.NO_ACTION

    def editMouseScroll(self, ev):
        """Called when the application is in edit mode and the mouse is released
        on the big label."""
        d = int(math.copysign(1, ev.delta())*math.sqrt(abs(ev.delta()))/self.lblBig.imageScaleRatio)
        if abs(d) < 1:
            d = d/abs(d)

        if self.selectedEditBox is not None:
            b = self.placedBoxes[self.selectedEditBox]
            (x1, y1, x2, y2) = b.static
            rat = (y2-y1)/float(x2-x1)
            (x1, y1, x2, y2) = (x1-d, y1-int(d*rat), x2+d ,y2+int(d*rat))
            (x1, y1, x2, y2) = (min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2))
            if abs(x1-x2) > 15 and abs(y1-y2) > 15:
                b.static = (x1,y1,x2,y2)

    def newBugIdEntered(self, bid):
        if self.removedBug != -1:
            self.placedBoxes[self.removedBug].name = bid
            self.setHintText(AppData.HINT_REPLACE_CONTINUE)
        elif self.selectedEditBox is not None and self.selectedEditBox != -1:
            self.placedBoxes[self.selectedEditBox].name = bid

    def quit(self):
        self.exportToCSV()
        QtCore.QCoreApplication.instance().quit()

    def setHintText(self, text):
        if self.controlPanel is not None:
            self.controlPanel.lblHint.setText(text)

    def onBugRemoved(self, i):
        if i != -1:
            self.controlPanel.setCurrentBugId(self.placedBoxes[i].name)
            self.selectedEditBox = -1
        else:
            self.controlPanel.setCurrentBugId('')

        self.removedBug = i

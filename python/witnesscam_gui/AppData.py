# Main driver for the application
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

from PySide import QtCore, QtGui
import cv2
import csv
import numpy as np
import os.path

from Pt import *
import Util
import Constants as C


class AppData(QtCore.QObject):
    """Main logic controler for the digitization gui"""

    sigSelectedBox = QtCore.Signal(int)
    sigDeletedBox = QtCore.Signal(int)
    sigCreatedBox = QtCore.Signal(int)
    sigTransformedBox = QtCore.Signal(int)
    sigShowHint = QtCore.Signal(str)

    # Types of editing actions for boxes
    NO_ACTION, DG_NW, DG_N, DG_NE, DG_E, DG_SE, DG_S, DG_SW, DG_W, PAN = \
        range(10)

    # Number of stable frames to wait before performing certain actions
    DRAW_DELTA = 10
    CAM_MAX_WIDTH = 640
    CAM_MAX_HEIGHT = 480
    BOX_RESIZE_EDGE_PADDING = 15

    def __init__(self, win, cv_impl, logger):
        """Initializes member variables for use in later functions"""

        super(AppData, self).__init__()

        self.window = win
        self.cvImpl = cv_impl
        self.logger = logger

        # Labels for displaying images
        self.barcodeEntry = None
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

        self.logger = logger
        self.logger.log("INIT AppData", 0)

        self.reset()

    def reset(self):
        """Reset internal attributes"""

        # Mouse position (current and last) on the big label
        self.mousePos = (0, 0)
        self.lastMousePos = (0, 0)

        # Variables used in keeping track of the placed boxes
        self.bugBoxList = Util.BugBoxList()
        self.removedBug = -1

        # Variables used for editing the boxes
        self.selectedEditBox = None
        self.editAction = AppData.NO_ACTION

        # Show Hint
        self.sigShowHint.emit(C.HINT_LOADFILE)

        self.logger.log("RESET AppData", 0)

    def setGuiElements(self, barcode, big, small):
        """Associate the elements of the gui with the application data.

        Keyword Arguments:
        barcode -- a BarcodeEntry instance
        big -- a BigLabel instance
        small -- a SmallLabel instance"""

        # Assign gui elements
        self.barcodeEntry = barcode
        self.lblBig = big
        self.lblSmall = small

        self.sigShowHint.emit(C.HINT_LOADFILE)

    @QtCore.Slot()
    def loadTrayImage(self, image_fname, csv_fname):
        """Load the tray scan image and activate the camera.

        Keyword Arguments:
        image_fname -- the string filepath of the tray scan image"""

        # Export current csv if there is one
        ret = self.exportToCSV()
        if not ret:
            return

        # Clear data
        self.reset()
        self.cvImpl.reset()
        self.barcodeEntry.setCurrentBugId("")

        # Load the image
        self.trayPath = image_fname
        self.logger.log("LOAD image scan file %s" % self.trayPath, 1)
        self.trayImage = cv2.imread(self.trayPath, cv2.IMREAD_COLOR)
        self.csvPath = csv_fname

        # Load csv file
        if os.path.isfile(csv_fname):
            with open(csv_fname) as csvfile:
                reader = csv.reader(csvfile)
                self.bugBoxList = Util.BugBoxList()

                if (reader.next()[1] == " Rectangle x1"):
                    for b in reader:
                        box = Util.BugBox(
                            b[0], None,
                            (int(b[1]), int(b[2]), int(b[3]), int(b[4])),
                            (int(b[5]), int(b[6])))
                        self.bugBoxList.newBox(box)

                    self.window.statusBar().showMessage(
                        "Also loaded CSV file: %s" %
                        str(os.path.split(csv_fname)[1]))
                    self.logger.log(
                        "LOAD found corresponding csv file %s"
                        % self.csvPath, 1)
                else:
                    QtGui.QMessageBox.information(
                        self.window, "Error Reading CSV",
                        "It seems the file %s id badly formatted. Cannot load."
                        % str(os.path.split(csv_fname)[1]))

        # Start the camera loop
        self.startCameraFeed()

        self.sigShowHint.emit(C.HINT_TRAYAREA_1)
        self.bugBoxList.clearUndoRedoStacks()

    def startCameraFeed(self):
        """Begin the camera feed and set up the timer loop."""

        if not self.camOn:
            self.capture = cv2.VideoCapture(0)

            self.frameTimer = QtCore.QTimer()
            self.frameTimer.timeout.connect(self.getNewCameraFrame)
            self.frameTimer.start(30)
            self.camOn = True
            self.logger.log("INIT camera", 0)

    def getNewCameraFrame(self):
        """This function is called by the timer 30 times a second to fetch a new
        frame from the camera, have it processed, and display the final result
        to on screen."""

        # Get new camera frame and downsample it
        (_, self.cameraImage) = self.capture.read()
        while (self.cameraImage.shape[0] > AppData.CAM_MAX_HEIGHT or
               self.cameraImage.shape[1] > AppData.CAM_MAX_WIDTH):
            self.cameraImage = cv2.pyrDown(self.cameraImage)

        # Process and modify the camera and static frames
        (big_image, small_image, self.bugBoxList) = self.cvImpl.amendFrame(
            self.cameraImage, self.trayImage, self.lblBig.imageScaleRatio,
            self.lblSmall.imageScaleRatio, self.bugBoxList)

        if self.cvImpl.allowEditing():
            dB = int(AppData.DRAW_DELTA/self.lblBig.imageScaleRatio)
            self.draw_editing_ui(big_image, C.GREEN, C.RED, C.BLUE, dB)

        # Display the modified frame to the user
        self.lblBig.setImage(big_image)
        self.lblSmall.setImage(small_image)

    def setMousepos(self, x, y):
        """Update the current mouse position"""

        self.mousePos = (x, y)

    def draw_editing_ui(self, image, regular, selected, active, a):
        """Given an input image, draw all of the generated boxes on the image.
        Optional colour paramaters can also be supplied.

        Keyword Arguments:
        image -- the numpy array image that the boxes will be drawn on
        regular -- the colour of the boxes
        selected -- the colour of the selected box
        """

        for i in range(len(self.bugBoxList)):
            b = self.bugBoxList[i].static
            (px, py) = self.bugBoxList[i].point
            t = max(int(a/5), 1)
            col = None

            if i == self.selectedEditBox:
                # Draw box
                cv2.rectangle(image, b[0:2], b[2:4], selected, t)

                # Draw delete button
                cv2.rectangle(image, (b[2]-a, b[1]+3*a), (b[2]-3*a, b[1]+a),
                              selected, t)
                cv2.line(image, (b[2]-a, b[1]+3*a), (b[2]-3*a, b[1]+a),
                         selected, t)
                cv2.line(image, (b[2]-3*a, b[1]+3*a), (b[2]-a, b[1]+a),
                         selected, t)

                # Draw Box ID
                ((_, h), _) = cv2.getTextSize(
                    self.bugBoxList[i].name, cv2.FONT_HERSHEY_SIMPLEX, a/18.0,
                    t)
                cv2.putText(image, self.bugBoxList[i].name,
                            (b[0]-int(a/2), b[3]+h), cv2.FONT_HERSHEY_SIMPLEX,
                            a/18.0, C.WHITE, t)
                col = selected
            else:
                col = regular

            # Draw point marker
            if i != self.removedBug:
                cv2.line(image, (px, py-a), (px, py+a), col, t)
                cv2.line(image, (px+a, py), (px-a, py), col, t)
                cv2.circle(image, (px, py), a, col, t)

    def exportToCSV(self):
        """Exports the bugBoxList data to a CSV file"""

        if self.csvPath is None or self.csvPath == "":
            return True

        ret = QtGui.QMessageBox.Save
        message = QtGui.QMessageBox()
        if os.path.isfile(self.csvPath):
            message.setText(C.DIALOG_OVERWRITE
                            % str(os.path.split(self.csvPath)[1]))
        else:
            message.setText(C.DIALOG_SAVE
                            % str(os.path.split(self.csvPath)[1]))

        message.setStandardButtons(
            QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard
            | QtGui.QMessageBox.Cancel)
        message.setDefaultButton(QtGui.QMessageBox.Save)
        ret = message.exec_()

        if ret == QtGui.QMessageBox.Save:
            f = open(self.csvPath, "w")
            f.write("Insect Id, Rectangle x1, y1, x2, y1, Point x, y\n")
            for b in self.bugBoxList:
                f.write(b.name + ", " +
                        str(b.getStaticBox())[1:-1] + ", " +
                        str(b.getPoint())[1:-1] + "\n")
            self.window.statusBar().showMessage(
                "Saved data to %s" % str(os.path.split(self.csvPath)[1]))
            return True
        elif ret == QtGui.QMessageBox.Discard:
            return True
        elif ret == QtGui.QMessageBox.Cancel:
            return False

    @QtCore.Slot()
    def mousePress(self, ev, scale):
        """When the mouse is clicked on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object
        scale -- scale constant between the size of the label and the size
            of the big label"""

        if self.trayPath is not None:
            self.cvImpl.mousePress(ev, scale)

        if self.cvImpl.allowEditing():
            self.editMousePress(ev)

    @QtCore.Slot()
    def mouseMove(self, ev, scale):
        """When the mouse is clicked on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object
        scale -- scale constant between the size of the label and the size
            of the big label"""

        self.setMousepos(int(ev.pos().x()/scale),
                         int(ev.pos().y()/scale))
        self.lblBig.setCursor(self.normalCursor)

        if self.trayPath is not None:
            self.cvImpl.mouseMove(ev, scale)

        if self.cvImpl.allowEditing():
            self.editMouseMove()

    @QtCore.Slot()
    def mouseRelease(self, ev, scale):
        """When the mouse is clicked on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object"""

        if self.trayPath is not None:
            self.cvImpl.mouseRelease(ev, scale)
        if self.cvImpl.allowEditing():
            self.editMouseRelease()

    @QtCore.Slot()
    def mouseScroll(self, ev, scale):
        """When the mouse is clicked on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object"""
        self.cvImpl.mouseScroll(ev, scale)
        if self.cvImpl.allowEditing():
            self.editMouseScroll(ev)

    def editMousePress(self, ev):
        """Called when the application is in edit mode and the mouse is clicked
        on the big label.

        Keyword Arguments:
        ev -- PySide.QtGui.QMouseEvent object"""

        (mx, my) = self.mousePos
        pad = AppData.BOX_RESIZE_EDGE_PADDING
        sp = int(AppData.DRAW_DELTA/self.lblBig.imageScaleRatio)

        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            if self.selectedEditBox is not None:
                # If a box is selected, check for clicking on an editable point
                # (e. corners for resizing, center for panning)
                p = self.mousePos
                (x1, y1, x2, y2) =\
                    self.bugBoxList[self.selectedEditBox].static

                if Util.pointInBox(p, (x2-3*sp, y1+sp, x2-sp, y1+3*sp)):
                    self.bugBoxList.delete(self.selectedEditBox)
                    self.selectedEditBox = None
                    self.sigDeletedBox.emit(self.selectedEditBox)
                    self.barcodeEntry.setCurrentBugId("")
                elif Util.pointInBox(p, (x1-pad, y1-pad, x1+pad, y1+pad)):
                    self.editAction = AppData.DG_NW
                elif Util.pointInBox(p, (x2-pad, y2-pad, x2+pad, y2+pad)):
                    self.editAction = AppData.DG_SE
                elif Util.pointInBox(p, (x1-pad, y2-pad, x1+pad, y2+pad)):
                    self.editAction = AppData.DG_SW
                elif Util.pointInBox(p, (x2-pad, y1-pad, x2+pad, y1+pad)):
                    self.editAction = AppData.DG_NE
                elif Util.pointInBox(p, (x1+pad, y1-pad, x2-pad, y1+pad)):
                    self.editAction = AppData.DG_N
                elif Util.pointInBox(p, (x1+pad, y2-pad, x2-pad, y2+pad)):
                    self.editAction = AppData.DG_S
                elif Util.pointInBox(p, (x1-pad, y1+pad, x1+pad, y2-pad)):
                    self.editAction = AppData.DG_W
                elif Util.pointInBox(p, (x2-pad, y1+pad, x2+pad, y2-pad)):
                    self.editAction = AppData.DG_E
                elif Util.pointInBox(p, (x1+pad, y1+pad, x2-pad, y2-pad)):
                    self.editAction = AppData.PAN

                if self.editAction != AppData.NO_ACTION:
                    return

            # If a box is not selected, check for clicking on a box to
            # to select it
            clickedOn = False
            for i in range(len(self.bugBoxList)):
                (x1, y1, x2, y2) = self.bugBoxList[i].static
                if Util.pointInBox((mx, my), (x1-pad, y1-pad, x2+pad, y2+pad)):
                    self.sigSelectedBox.emit(i)
                    clickedOn = True
                    self.selectedEditBox = i
                    self.barcodeEntry.setCurrentBugId(self.bugBoxList[i].name)
                    self.sigShowHint.emit(C.HINT_EDITBOX)

            # Check for deselect of box
            if not clickedOn:
                self.selectedEditBox = None
                self.sigShowHint.emit(C.HINT_REMOVEBUG)
                self.barcodeEntry.setCurrentBugId("")
        else:
            box = Util.BugBox("Box %s" % str(len(self.bugBoxList)),
                              None,
                              (mx-3*sp, my-3*sp, mx+3*sp, my+3*sp),
                              (mx, my))
            self.bugBoxList.newBox(box)
            self.selectedEditBox = len(self.bugBoxList) - 1
            self.barcodeEntry.setCurrentBugId(
                self.bugBoxList[self.selectedEditBox].name)

    def editMouseMove(self):
        """Called when the application is in edit mode and the mouse is moved
        on the big label."""

        p = self.mousePos

        # Show box select cursor if hovered over box
        self.lblBig.setCursor(self.normalCursor)
        for b in self.bugBoxList:
            if Util.pointInBox(p, b.static):
                self.lblBig.setCursor(self.selectCursor)

        if self.selectedEditBox is not None:
            if self.editAction == AppData.NO_ACTION:
                # If box is selected, show various cursors for editing functions
                pad = AppData.BOX_RESIZE_EDGE_PADDING
                sp = int(AppData.DRAW_DELTA/self.lblBig.imageScaleRatio)
                (x1, y1, x2, y2) =\
                    self.bugBoxList[self.selectedEditBox].static
                if Util.pointInBox(p, (x2-3*sp, y1+sp, x2-sp, y1+3*sp)):
                    self.lblBig.setCursor(self.deleteCursor)
                elif Util.pointInBox(p, (x1-pad, y1-pad, x1+pad, y1+pad)):
                    self.lblBig.setCursor(self.resizeCursorF)
                elif Util.pointInBox(p, (x2-pad, y2-pad, x2+pad, y2+pad)):
                    self.lblBig.setCursor(self.resizeCursorF)
                elif Util.pointInBox(p, (x1-pad, y2-pad, x1+pad, y2+pad)):
                    self.lblBig.setCursor(self.resizeCursorB)
                elif Util.pointInBox(p, (x2-pad, y1-pad, x2+pad, y1+pad)):
                    self.lblBig.setCursor(self.resizeCursorB)
                elif Util.pointInBox(p, (x1+pad, y1-pad, x2-pad, y1+pad)):
                    self.lblBig.setCursor(self.resizeCursorV)
                elif Util.pointInBox(p, (x1+pad, y2-pad, x2-pad, y2+pad)):
                    self.lblBig.setCursor(self.resizeCursorV)
                elif Util.pointInBox(p, (x1-pad, y1+pad, x1+pad, y2-pad)):
                    self.lblBig.setCursor(self.resizeCursorH)
                elif Util.pointInBox(p, (x2-pad, y1+pad, x2+pad, y2-pad)):
                    self.lblBig.setCursor(self.resizeCursorH)
                elif Util.pointInBox(p, (x1+pad, y1+pad, x2-pad, y2-pad)):
                    self.lblBig.setCursor(self.prepanCursor)
            else:
                # If active action, then modify the box
                (dx, dy) = (self.mousePos[0] - self.lastMousePos[0],
                            self.mousePos[1] - self.lastMousePos[1])
                b = self.bugBoxList[self.selectedEditBox]
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

                self.bugBoxList.changeBox(
                    self.selectedEditBox, static=newBox, point=newPoint)

        self.lastMousePos = self.mousePos

    def editMouseRelease(self):
        """Called when the application is in edit mode and the mouse is released
        on the big label."""

        if self.editAction != AppData.NO_ACTION and self.selectedEditBox != -1:
            self.sigTransformedBox.emit(self.selectedEditBox)

        self.editAction = AppData.NO_ACTION

    def editMouseScroll(self, ev):
        """Called when the application is in edit mode and the mouse is released
        on the big label."""

        d = int(math.copysign(1, ev.delta())
                * math.sqrt(abs(ev.delta()))/self.lblBig.imageScaleRatio)
        if abs(d) < 1:
            d = d/abs(d)

        if self.selectedEditBox is not None:
            self.sigTransformedBox.emit(self.selectedEditBox)
            b = self.bugBoxList[self.selectedEditBox]
            (x1, y1, x2, y2) = b.static
            rat = (y2-y1)/float(x2-x1)
            (x1, y1, x2, y2) = (x1-d, y1-int(d*rat), x2+d, y2+int(d*rat))
            (x1, y1, x2, y2) = (min(x1, x2), min(y1, y2),
                                max(x1, x2), max(y1, y2))
            if abs(x1-x2) > 15 and abs(y1-y2) > 15:
                self.bugBoxList.changeBox(
                    self.selectedEditBox, static=(x1, y1, x2, y2))

    @QtCore.Slot()
    def newBugIdEntered(self, bid):
        """This function is called when a new id has been selected for the
        currently selected bug.

        Keyword Arguments:
        bid -- the string bug id"""

        if self.removedBug != -1:
            self.bugBoxList.changeBox(self.removedBug, name=bid)
            self.sigShowHint.emit(C.HINT_REPLACE_CONTINUE)
        elif self.selectedEditBox is not None and self.selectedEditBox != -1:
            self.bugBoxList.changeBox(self.selectedEditBox, name=bid)

    @QtCore.Slot()
    def quit(self):
        """Promtps user to save work, and quits the application"""

        exit = self.exportToCSV()
        if exit:
            self.logger.stop()
            QtCore.QCoreApplication.instance().quit()

    @QtCore.Slot()
    def onBugRemoved(self, i):
        """Updates the current state when a bug has been removed.

        Keyword Arguments:
        i -- index in bugBoxList of the recently removed bug"""
        if i != -1:
            self.barcodeEntry.setCurrentBugId(self.bugBoxList[i].name)
            self.selectedEditBox = None
        else:
            self.barcodeEntry.setCurrentBugId("")

        self.removedBug = i

    @QtCore.Slot()
    def undoAction(self):
        """Process the user's request to undo the previous action."""

        # Call cvImpl's undo first. If nothing happens, then undo box actions
        if not self.cvImpl.undo():
            i = self.bugBoxList.undo()
            self.sigSelectedBox.emit(i)
            self.selectedEditBox = i
            if i >= 0 and i < len(self.bugBoxList):
                self.barcodeEntry.setCurrentBugId(self.bugBoxList[i].name)

    @QtCore.Slot()
    def redoAction(self):
        """Process the user's request to redo the previous action."""

        # Call cvImpl's redo first. If nothing happens, then redo box actions
        if not self.cvImpl.redo():
            i = self.bugBoxList.redo()
            self.sigSelectedBox.emit(i)
            self.selectedEditBox = i
            if i >= 0 and i < len(self.bugBoxList):
                self.barcodeEntry.setCurrentBugId(self.bugBoxList[i].name)

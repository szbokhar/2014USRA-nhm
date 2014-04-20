# Button panel to be used in the segmentation program
#
# Technology for Nature. British Natural History Museum insect specimen
# segmentation project.
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

from PySide import QtGui, QtCore
from ImagePanel import *

class ToolPanel(QtGui.QFrame):

    # Signals emitted by the tool pane
    sigOpenFile = QtCore.Signal(str)
    sigClearTemplate = QtCore.Signal()

    def __init__(self, segData, parent=None):
        super(ToolPanel, self).__init__(parent)
        self.currentPath = "."
        self.initUI()
        self.data = segData

    # Setup Tool Pane gui
    def initUI(self):
        # Setup Buttons
        self.btnOpenImage = QtGui.QPushButton("Open Image")
        self.btnOpenImage.setMinimumHeight(50)
        self.btnOpenImage.setStatusTip("Open a new image of specimines")

        self.btnSelectTemplate = QtGui.QPushButton("Select Template")
        self.btnSelectTemplate.setMinimumHeight(50)
        self.btnSelectTemplate.setStatusTip("Make a new template selection")

        self.btnNextBug = QtGui.QPushButton("Select\nBug")
        self.btnNextBug.setMinimumHeight(50)
        self.btnNextBug.setStatusTip("Specify the next bug")

        self.btnCancelBug = QtGui.QPushButton("Cancel\nSelection")
        self.btnCancelBug.setMinimumHeight(50)
        self.btnCancelBug.setStatusTip("Cancel bug selection")
        self.btnCancelBug.setEnabled(False)

        self.btnSelectBox = QtGui.QPushButton("Select Exsisting Box")
        self.btnSelectBox.setMinimumHeight(50)

        self.btnSaveBoxes = QtGui.QPushButton("Save Boxes to File")
        self.btnSaveBoxes.setMinimumHeight(50)

        # Empty Space
        frmEmpty = QtGui.QFrame(self)

        # Add button to panel
        content = QtGui.QGridLayout()
        content.addWidget(self.btnOpenImage, 0, 0, 1, 2)
        content.addWidget(self.btnSelectTemplate, 1, 0, 1, 2)
        content.addWidget(self.btnNextBug, 2, 0)
        content.addWidget(self.btnCancelBug, 2, 1)
        content.addWidget(self.btnSelectBox, 3, 0, 1, 2)
        content.addWidget(self.btnSaveBoxes, 4, 0, 1, 2)
        content.addWidget(frmEmpty, 5, 0, 1, 2)

        # Finish up pane
        self.setLayout(content)
        self.show()

    # Setup slots for signals from the image pane
    def setImagePane(self, img):
        self.btnOpenImage.clicked.connect(self.openFile)
        self.btnSaveBoxes.clicked.connect(self.saveFile)
        img.sigTemplate.connect(self.newTemplateSelected)
        img.sigBugSelection.connect(self.bugSelection)
        img.sigBoxSelection.connect(self.boxSelection)

    # Open a new image file
    def openFile(self):
        fname, _ = QtGui.QFileDialog.getOpenFileName(self, "Open Specimin File",
                        self.currentPath)

        if fname != "":
            fpath = fname.split("/")
            self.currentPath = "/".join(fpath[0:-1])
            self.sigOpenFile.emit(fname)

    # Save a csv file
    def saveFile(self):
        fname, _ = QtGui.QFileDialog.getSaveFileName(self, "Save Boxes CSV File",
                        self.currentPath)

        if fname != "":
            self.data.saveCSV(fname)

    # Called when the user has finished selecting a new template
    def newTemplateSelected(self, ev):
        if ev == "ButtonPressed":
            self.btnNextBug.setEnabled(False)
            self.btnCancelBug.setEnabled(False)
            self.btnSelectBox.setEnabled(False)
        elif ev == "TemplateSelected":
            self.btnSelectTemplate.setText("Reset Template")
            self.btnNextBug.setEnabled(True)
            self.btnSelectBox.setEnabled(True)

    def bugSelection(self, result):
        if result == "Confirmed":
            self.btnCancelBug.setEnabled(True)
            self.btnNextBug.setText("Confirm\nBug")
            self.btnNextBug.setEnabled(True)
        elif result == "Cancelled":
            self.btnCancelBug.setEnabled(False)
            self.btnNextBug.setText("Select\nBug")
            self.btnSelectTemplate.setEnabled(True)
            self.btnSelectBox.setEnabled(True)
        elif result == "Start":
            self.btnCancelBug.setEnabled(True)
            self.btnNextBug.setText("Confirm\nBug")
            self.btnSelectTemplate.setEnabled(False)
            self.btnSelectBox.setEnabled(False)
            self.btnNextBug.setEnabled(False)

    def boxSelection(self, result):
        if result == "BoxSelectOn":
            self.btnSelectBox.setText("Cancel Selection")
            self.btnCancelBug.setText("Delete\nBox")
            self.btnSelectTemplate.setEnabled(False)
            self.btnNextBug.setEnabled(False)
            self.btnCancelBug.setEnabled(True)
        elif result == "BoxSelectOff":
            self.btnSelectBox.setText("Select Exsisting Box")
            self.btnCancelBug.setText("Cancel\nSelection")
            self.btnSelectTemplate.setEnabled(True)
            self.btnNextBug.setEnabled(True)
            self.btnCancelBug.setEnabled(False)

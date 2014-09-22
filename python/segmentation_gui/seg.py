# Main python program for interactive insect specimen segmentation
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

import sys
from PySide import QtGui, QtCore
from ToolPanel import *
from ImagePanel import *
from Segmentation import *

class MainWindow(QtGui.QMainWindow):

    def __init__(self, fname=None):
        super(MainWindow, self).__init__()
        self.initUI(fname)

    # Initialize UI
    def initUI(self, fname=None):

        # Setup main content area
        mainWidget = QtGui.QFrame(self)
        mainContent = QtGui.QHBoxLayout(self)

        # Setup main panels and segmentation data
        data = SegmentationData(fname)
        imagePane = ImagePanel(data, self)
        toolPane = ToolPanel(data, self)

        # Pair the tool pane and image pane
        toolPane.setImagePane(imagePane)
        imagePane.setToolPane(toolPane)

        # Put both panes in a splitter
        splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter1.addWidget(toolPane)
        splitter1.addWidget(imagePane)
        splitter1.setSizes([1,500])

        # Add splitter to the main window
        mainContent.addWidget(splitter1)
        mainWidget.setLayout(mainContent)
        self.setCentralWidget(mainWidget)

        # Finish up window
        self.statusBar().showMessage("Ready")
        self.setGeometry(0, 0, 1024, 720)
        self.setFixedSize(self.size())
        self.setWindowTitle('Insect Segmentation')
        self.show()

def main():
    logfile = None
    if len(sys.argv) > 1:
        logfile = sys.argv[1]

    app = QtGui.QApplication(sys.argv)
    ex = MainWindow(logfile)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

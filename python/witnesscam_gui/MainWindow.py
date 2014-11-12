from PySide import QtCore, QtGui

from AppData import *
from GUIParts import *


class MainWindow(QtGui.QMainWindow):

    def __init__(self, fname=None):
        super(MainWindow, self).__init__()
        self.initUI(fname)

    def initUI(self, fname=None):
        # Setup main content area
        mainWidget = QtGui.QFrame(self)
        mainContent = QtGui.QVBoxLayout(self)

        # Setup Gui Elements
        self.data = AppData()
        self.controlPanel = ControlPanel(self.data)
        self.lblBig = BigLabel(self.data)
        self.lblsmall = SmallLabel(self.data)
        self.data.setGuiElements(self.controlPanel, self.lblBig, self.lblsmall)

        self.topPanel = QtGui.QFrame()
        self.topContent = QtGui.QHBoxLayout(self)

        # Add GUI elements to window
        mainWidget.setLayout(mainContent)
        self.topPanel.setLayout(self.topContent)
        self.setCentralWidget(mainWidget)

        mainContent.addWidget(self.topPanel)
        mainContent.addWidget(self.controlPanel)
        self.topContent.addWidget(self.lblBig)
        self.topContent.addWidget(self.lblsmall)

        # Finish up window
        self.statusBar().showMessage("Ready")
        self.setGeometry(0, 0, 1024, 720)
        self.setFixedSize(self.size())
        self.setWindowTitle('Insect Segmentation')
        self.show()

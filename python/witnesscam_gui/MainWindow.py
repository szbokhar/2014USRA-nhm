from PySide import QtCore, QtGui

from AppData import *
from GUIParts import *


class MainWindow(QtGui.QMainWindow):

    originalSize = (1024, 600)

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
        self.lblSmall = SmallLabel(self.data)
        self.data.setGuiElements(self.controlPanel, self.lblBig, self.lblSmall)

        self.topPanel = QtGui.QFrame()
        self.topContent = QtGui.QHBoxLayout(self)

        # Add GUI elements to window
        mainWidget.setLayout(mainContent)
        self.topPanel.setLayout(self.topContent)
        self.setCentralWidget(mainWidget)

        mainContent.addWidget(self.topPanel)
        mainContent.addWidget(self.controlPanel)
        self.topContent.addWidget(self.lblBig)
        self.topContent.addWidget(self.lblSmall)

        # Finish up window
        self.statusBar().showMessage("Ready")
        self.setGeometry(0, 0, self.originalSize[0], self.originalSize[1])
        self.setWindowTitle('Insect Segmentation')
        self.show()

    def resizeEvent(self, ev):
        h = ev.size().height()
        w = ev.size().width()
        (oldW, oldH) = self.originalSize
        scale = (float(w)/oldW, float(h)/oldH)
        self.lblBig.newResizeScale(scale)
        self.lblSmall.newResizeScale(scale)

    def closeEvent(self, event):
        self.data.quit()

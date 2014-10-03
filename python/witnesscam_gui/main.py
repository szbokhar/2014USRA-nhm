from PySide import QtCore, QtGui
import cv2
import sys

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
        self.bigLabel = BigLabel(self.data)
        self.smallLabel = SmallLabel(self.data)

        self.topPanel = QtGui.QFrame()
        self.topContent = QtGui.QHBoxLayout(self)

        # Add GUI elements to window
        mainWidget.setLayout(mainContent)
        self.topPanel.setLayout(self.topContent)
        self.setCentralWidget(mainWidget)

        mainContent.addWidget(self.topPanel)
        mainContent.addWidget(self.controlPanel)
        self.topContent.addWidget(self.bigLabel)
        self.topContent.addWidget(self.smallLabel)

        # Finish up window
        self.statusBar().showMessage("Ready")
        self.setGeometry(0, 0, 1024, 720)
        self.setFixedSize(self.size())
        self.setWindowTitle('Insect Segmentation')
        self.show()


class AppData:

    def __init__(self):
        None

class ControlPanel(QtGui.QFrame):

    def __init__(self, data, parent=None):
        super(ControlPanel, self).__init__(parent)
        self.data = data
        self.initUI()

    def initUI(self):
        panelLayout = QtGui.QHBoxLayout(self)
        self.setLayout(panelLayout)

        self.btnLoadTray = QtGui.QPushButton("Load Tray Scan")
        self.btnLoadTray.setMinimumHeight(50)
        self.btnLoadTray.setStatusTip("Load Tray Scan")

        self.btnQuit = QtGui.QPushButton("Quit")
        self.btnQuit.setMinimumHeight(50)
        self.btnQuit.setStatusTip("Quit")

        panelLayout.addWidget(self.btnLoadTray)
        panelLayout.addWidget(self.btnQuit)

class BigLabel(QtGui.QLabel):

    def __init__(self, data, parent=None):
        super(BigLabel, self).__init__(parent)
        self.data = data
        self.initUI()

    def initUI(self):
        self.setFixedSize(QtCore.QSize(640, 480))
        self.setText('Big')

class SmallLabel(QtGui.QLabel):

    def __init__(self, data, parent=None):
        super(SmallLabel, self).__init__(parent)
        self.data = data
        self.initUI()

    def initUI(self):
        self.setFixedSize(QtCore.QSize(300, 200))
        self.setText('Small')

def main():
    logfile = None
    if len(sys.argv) > 1:
        logfile = sys.argv[1]

    app = QtGui.QApplication(sys.argv)
    ex = MainWindow(logfile)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

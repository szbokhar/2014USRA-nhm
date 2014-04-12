import sys
from PySide import QtGui, QtCore
from ToolPanel import *
from ImagePanel import *
from Segmentation import *

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    # Initialize UI
    def initUI(self):

        # Setup main content area
        mainWidget = QtGui.QFrame(self)
        mainContent = QtGui.QHBoxLayout(self)

        # Setup main panels and segmentation data
        data = SegmentationData()
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

    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

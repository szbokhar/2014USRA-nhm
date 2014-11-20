from MainWindow import *
from WitnessCam import *


def main():
    logfile = None
    if len(sys.argv) > 1:
        logfile = sys.argv[1]

    app = QtGui.QApplication(sys.argv)
    wc = WitnessCam()
    ex = MainWindow(wc, logfile)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

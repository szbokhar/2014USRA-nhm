from MainWindow import *

def main():
    logfile = None
    if len(sys.argv) > 1:
        logfile = sys.argv[1]

    app = QtGui.QApplication(sys.argv)
    ex = MainWindow(logfile)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()


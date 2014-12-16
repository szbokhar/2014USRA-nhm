# Main python program
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

import sys
import os

from MainWindow import *
from WitnessCam import *
from Util import InteractionLogger

def main():
    logfile = None
    testfile = None

    i = 0
    while i < len(sys.argv):
        if sys.argv[i] == '-l':
            logfile = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == '-t':
            testfile = sys.argv[i+1]
            i += 2
        else:
            i += 1

    logger = InteractionLogger(logfile)
    logger.start()
    tester = TestingData.loadTestingFile(testfile)
    app = QtGui.QApplication(sys.argv)
    wc = WitnessCam(logger, tester)
    ex = MainWindow(wc, logger, tester)

    if tester is not None and tester.automate:
        tester.setMainTestingWindow(ex)
        tester.runtest()
    else:
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()

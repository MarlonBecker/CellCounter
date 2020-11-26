import sys
#quit when ctrl+c is pressed in console
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt5.QtWidgets import QApplication

from gui.mainWindow import MainWindow


"""
@TODO
    - do not use '../' to find file path of settings file
    - when error occured, stop thread until message box is closed
    - make exposure setable by texbox
"""

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(open('resources/pyQtStyleSheet.css').read())

    win = MainWindow()
    # win.showMaximized()
    win.showFullScreen()
    win.setWindowTitle("Cell Counter")
    sys.exit(app.exec_())

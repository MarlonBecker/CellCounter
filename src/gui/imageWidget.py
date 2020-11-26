import cv2
import numpy as np

from PyQt5.QtCore import  QPoint, QTimer
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QImage

import constants

class ImageWidget(QWidget):
    """Widget to dispay image."""
    def __init__(self, queue, parent=None):
        super(ImageWidget, self).__init__(parent)

        self.imageQueue = queue

        # Timer to trigger display
        self.showTimer = QTimer(self)
        self.showTimer.setInterval(constants.DISP_MSEC)
        self.showTimer.timeout.connect(self.showQueueImage)
        self.startShowLive = self.showTimer.start
        self.stopShowLive  = self.showTimer.stop


        self.displayImage   = None
        self.fullImage      = None
        self.annotatedImage = None

    def showQueueImage(self):
        """Display image from self.imageQueue to screen"""
        if self.imageQueue.empty():
            return
        self.displayImage = self.imageQueue.get()
        if self.displayImage is not None and len(self.displayImage) > 0:
            self.update()

    def markCells(self, cells):
        self.annotatedImage = np.copy(self.fullImage)
        for cell in cells:
            self.annotatedImage = cv2.drawMarker(self.annotatedImage, cell, (255,0,0), cv2.MARKER_CROSS, thickness = 4, markerSize = 30)

        cv2.putText(self.annotatedImage,str(len(cells)),
                    (5, constants.CAMERA_RESOLUTION[0]-20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    10,
                    (255,255,255),
                    thickness = 10,
                    bottomLeftOrigin = False)

        self.displayImage = cv2.resize(self.annotatedImage, constants.DISPLAY_RESOLUTION[::-1], interpolation=cv2.INTER_CUBIC)
        self.update()


    def shwoFullImage(self, fullImage):
        self.fullImage = fullImage

        self.displayImage = cv2.resize(self.fullImage, constants.DISPLAY_RESOLUTION[::-1], interpolation=cv2.INTER_CUBIC)
        self.update()



    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        if not constants.settings["show"]["Red"  ]: self.displayImage[:,:,0] = 0
        if not constants.settings["show"]["Green"]: self.displayImage[:,:,1] = 0
        if not constants.settings["show"]["Blue" ]: self.displayImage[:,:,2] = 0

        if isinstance(self.displayImage, np.ndarray):
            qImage = QImage(self.displayImage.data, constants.DISPLAY_RESOLUTION[1], constants.DISPLAY_RESOLUTION[0], QImage.Format_RGB888)
            qp.drawImage(QPoint(0, 0), qImage)
        qp.end()

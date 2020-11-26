import os
import queue as Queue
import threading
from datetime import datetime
import numpy as np
import cv2

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QShortcut, QStackedWidget, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtGui import QKeySequence

from logger import logger
from count import getCells
import util


from gui.imageWidget import ImageWidget
from gui.settingsWidget import SettingsWidget
from hardwareHandler import HardwareHandler


class MainWindow(QMainWindow):
    errorSignal          = pyqtSignal(str) #emitted when errors occur. error box with message msg is opened by main thread
    countingDoneSignal   = pyqtSignal()
    triggeringDoneSignal = pyqtSignal()
    backToPreviewSignal  = pyqtSignal()

    def __init__(self):
        super(MainWindow, self).__init__()

        self.errorSignal         .connect(self.openErrorMessage)
        self.countingDoneSignal  .connect(self.countingDone)
        self.triggeringDoneSignal.connect(self.triggeringDone)
        self.backToPreviewSignal .connect(self.backToPreview)

        self.cellsQueue = Queue.Queue()     # queue to pass cell coordinates found by counting algorithm
        self.imageQueue = Queue.Queue()     # Queue to hold images

        self.mode = None # "Color" or "UV"


        util.loadSettings()

        self.hardwareHandler = HardwareHandler(self.imageQueue)


        #####  shortcuts ####
        self.quitSC = QShortcut(QKeySequence('Ctrl+Q'), self)
        self.quitSC.activated.connect(QApplication.instance().quit)

        self.exitFS = QShortcut("ESC", self)
        self.exitFS.activated.connect(self.showMaximized)


        def switchMaxFS():
            if self.isFullScreen():
                self.showNormal() #workaround... if showNormal is not called in between, showMaxize does not work...
                self.showMaximized()
            else:                 self.showFullScreen()
        self.switchMaxFS = QShortcut(QKeySequence('Ctrl+F'), self)
        self.switchMaxFS.activated.connect(switchMaxFS)




        ############# layout #############
        self.centralWidget = QWidget(self)
        self.hlayout       = QHBoxLayout()

        #####  image view #####
        self.imageWidget = ImageWidget(self.imageQueue, self)
        self.hlayout.addWidget(self.imageWidget)

        #####  control widget #####
        self.controlWidget = QStackedWidget()
        self.controlWidget.setMaximumWidth(320)

        ## page 1 - main page##
        self.page1Widget = QWidget(self.controlWidget)
        self.page1Layout = QVBoxLayout()
        self.page1Widget.setLayout(self.page1Layout)

        buttonTrigger        = QPushButton("&Trigger")
        buttonSettings       = QPushButton("&Settings")
        buttonTriggerAndSave = QPushButton("Trigger + Save")
        self.buttonMode      = QPushButton("Switch to ...")
        buttonTrigger       .clicked.connect(self.trigger)
        buttonSettings      .clicked.connect(lambda: self.controlWidget.setCurrentIndex(2))
        buttonSettings      .clicked.connect(lambda: self.infoTextBox.setText(""))
        buttonTriggerAndSave.clicked.connect(self.triggerAndSave)
        self.buttonMode     .clicked.connect(lambda: self.changeMode())
        self.page1Layout.addWidget(buttonTrigger)
        self.page1Layout.addWidget(self.buttonMode)
        self.page1Layout.addWidget(buttonSettings)
        self.page1Layout.addWidget(buttonTriggerAndSave)


        ## page 2 - image captured##
        self.page2Widget = QWidget(self.controlWidget)
        self.page2Layout = QVBoxLayout()
        self.page2Widget.setLayout(self.page2Layout)


        buttonBackToPreview = QPushButton("&Back")
        buttonSaveImage     = QPushButton("&Save")
        buttonCount         = QPushButton("&Count")
        buttonBackToPreview.clicked.connect(self.backToPreview)
        buttonSaveImage    .clicked.connect(lambda: self.saveImage())
        buttonCount        .clicked.connect(self.startCounting)
        self.page2Layout.addWidget(buttonBackToPreview)
        self.page2Layout.addWidget(buttonSaveImage)
        self.page2Layout.addWidget(buttonCount)


        ## page 3 - settings ##
        self.settingsWidget = SettingsWidget(self.controlWidget)
        self.settingsWidget.OKButton.clicked.connect(lambda: self.controlWidget.setCurrentIndex(0))
        self.settingsWidget.OKButton.clicked.connect(lambda: self.infoTextBox.setText("Live capturing"))

        # signals emitted when settings change
        self.settingsWidget.UVLEDSettingsUpdatedSignal     .connect(self.hardwareHandler.updateLEDUV)
        self.settingsWidget.ColorLEDSettingsUpdatedSignal  .connect(self.hardwareHandler.updateLEDColors)
        self.settingsWidget.captureSettingsUpdatedSignal   .connect(lambda : self.hardwareHandler.updateCaptureSettings(mode = self.mode))
        self.settingsWidget.resetSignal                    .connect(self.hardwareHandler.updateLEDUV)
        self.settingsWidget.resetSignal                    .connect(self.hardwareHandler.updateLEDColors)
        self.settingsWidget.resetSignal                    .connect(lambda : self.hardwareHandler.updateCaptureSettings(mode = self.mode))

        #set mode if tab is changed in settings widget
        def setModeFromTabIndex(tabIndex: int):
            if   tabIndex == 0: self.changeMode("Color")
            elif tabIndex == 1: self.changeMode("UV")
        self.settingsWidget.tabs.currentChanged.connect(setModeFromTabIndex)




        ## page 4 - counting ##
        self.page4Widget = QWidget(self.controlWidget)
        self.page4Layout = QVBoxLayout(self.page4Widget)

        # buttonStopCounting = QPushButton("&Stop Counting")
        # buttonStopCounting.clicked.connect(self.stopCounting)
        # self.page4Layout.addWidget(buttonStopCounting)
        countingLabel = QLabel("Counting..", alignment = Qt.AlignCenter)
        self.page4Layout.addWidget(countingLabel)


        ## page 5 - trigger and save ##
        self.page5Widget = QWidget(self.controlWidget)
        self.page5Layout = QVBoxLayout(self.page5Widget)
        self.triggerAndSaveLabel = QLabel("Capture color Image\t\n"
                                          "Save color Image\t\t\n"
                                          "Capture UV Image\t\n"
                                          "Save UV Image\t\t", alignment = Qt.AlignVCenter | Qt.AlignLeft)
        self.page5Layout.addWidget(self.triggerAndSaveLabel)



        self.controlWidget.addWidget(self.page1Widget)
        self.controlWidget.addWidget(self.page2Widget)
        self.controlWidget.addWidget(self.settingsWidget)
        self.controlWidget.addWidget(self.page4Widget)
        self.controlWidget.addWidget(self.page5Widget)
        self.hlayout.addWidget(self.controlWidget)


        self.hlayout.setContentsMargins(0,0,0,0)
        self.centralWidget.setLayout(self.hlayout)
        self.setCentralWidget(self.centralWidget)


        ## info in right bottom corner
        self.infoTextBox = QLabel(self.centralWidget)
        self.infoTextBox.setText("TEST")
        self.infoTextBox.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.infoTextBox.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) # pylint: disable=no-member
        self.installEventFilter( util.ObjectResizer(self, self.infoTextBox))


        logger.info("Gui started")
        # start capture and led
        self.changeMode("Color")
        self.imageWidget.startShowLive()
        self.infoTextBox.setText("Live capturing")

    # def stopCapturing(self):
    #     self.imageWidget.stopShowLive()
    #     self.hardwareHandler.stopCapturing()
    #     self.capture_thread.join()
    #     self.imageQueue.queue.clear()


    def changeMode(self, mode = None):
        if mode is None:
            if   self.mode == "UV"   : mode = "Color"
            elif self.mode == "Color": mode = "UV"

        if mode != self.mode:
            logger.info(f"Changing mode to '{mode}'.")

            self.mode = mode
            if self.mode == "UV":
                #update button text
                self.buttonMode.setText("Switch to Color")
                #update settings tab. block signals to acoid infinite cyclic signal calls
                self.settingsWidget.tabs.blockSignals(True)
                self.settingsWidget.tabs.setCurrentIndex(1)
                self.settingsWidget.tabs.blockSignals(False)
                #set leds
                self.hardwareHandler.switchCOLOR_LED(False)
                self.hardwareHandler.switchUV_LED   (True)
            elif self.mode == "Color":
                #update button text
                self.buttonMode.setText("Switch to UV")
                #update settings tab. block signals to acoid infinite cyclic signal calls
                self.settingsWidget.tabs.blockSignals(True)
                self.settingsWidget.tabs.setCurrentIndex(0)
                self.settingsWidget.tabs.blockSignals(False)
                #set leds
                self.hardwareHandler.switchCOLOR_LED(True)
                self.hardwareHandler.switchUV_LED   (False)


            self.hardwareHandler.updateCaptureSettings(mode = self.mode)

    ### button events ###
    def trigger(self):
        self.page1Widget.setEnabled(False)
        logger.info("Fetching image")
        self.infoTextBox.setText("Fetching image")
        self.imageWidget.stopShowLive()
        self.hardwareHandler.stopCapturing()

        def run():
            fullImage = self.hardwareHandler.shootImage_fullResolution(mode = self.mode)
            self.imageWidget.shwoFullImage(fullImage)
            self.triggeringDoneSignal.emit()

        thread = threading.Thread(target = run)
        thread.start()

    def triggeringDone(self):
        self.controlWidget.setCurrentIndex(1)
        self.page1Widget.setEnabled(True)
        self.infoTextBox.setText("Ready")

    def backToPreview(self):
        self.infoTextBox.setText("Live capturing")
        self.controlWidget.setCurrentIndex(0)

        self.imageWidget.annotatedImage = None
        self.hardwareHandler.startCapturing(mode = self.mode)
        self.imageWidget.startShowLive()

    def triggerAndSave(self):
        def run():
            #stop captureing
            self.imageWidget.stopShowLive()
            self.hardwareHandler.stopCapturing()
            #set gui info
            self.controlWidget.setCurrentIndex(4)
            self.triggerAndSaveLabel.setText("Capture color Image\t\n"
                                             "Save color Image\t\t\n"
                                             "Capture UV Image\t\n"
                                             "Save UV Image\t\t")
            # use timestamp for file names
            timeStamp = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")

            ########## color image ##########
            # set color leds
            self.hardwareHandler.switchCOLOR_LED(True)
            self.hardwareHandler.switchUV_LED   (False)
            #capture image
            fullImage = self.hardwareHandler.shootImage_fullResolution(mode = "Color")
            #show image
            self.imageWidget.shwoFullImage(fullImage)
            self.triggerAndSaveLabel.setText("Capture color Image\t-> done\n"
                                             "Save color Image\t\t\n"
                                             "Capture UV Image\t\n"
                                             "Save UV Image\t\t")
            self.saveImage(fileName=f"{timeStamp}_color")
            self.triggerAndSaveLabel.setText("Capture color Image\t-> done\n"
                                             "Save color Image\t\t-> done\n"
                                             "Capture UV Image\t\n"
                                             "Save UV Image\t\t")
            ########## UV image ##########
            # set UV leds
            self.hardwareHandler.switchCOLOR_LED(False)
            self.hardwareHandler.switchUV_LED   (True)
            #capture image
            fullImage = self.hardwareHandler.shootImage_fullResolution(mode = "UV")
            #show image
            self.imageWidget.shwoFullImage(fullImage)
            self.triggerAndSaveLabel.setText("Capture color Image\t-> done\n"
                                             "Save color Image\t\t-> done\n"
                                             "Capture UV Image\t-> done\n"
                                             "Save UV Image\t\t")
            self.saveImage(fileName=f"{timeStamp}_UV")
            self.triggerAndSaveLabel.setText("Capture color Image\t-> done\n"
                                             "Save color Image\t\t-> done\n"
                                             "Capture UV Image\t-> done\n"
                                             "Save UV Image\t\t")
            self.backToPreviewSignal.emit()

        thread = threading.Thread(target = run)
        thread.start()

    def startCounting(self):
        logger.info("Counting...")
        self.infoTextBox.setText("Counting...")

        self.countingThread = threading.Thread(target = self.count)
        self.countingThread.start()

        self.controlWidget.setCurrentIndex(3)

    # def stopCounting(self):
    #     logger.info("Counting stopped")
    #     self.infoTextBox.setText("Counting stopped")
    #     self.controlWidget.setCurrentIndex(1)


    def countingDone(self):
        logger.info("Counting done")
        self.infoTextBox.setText("Counting done")

        cells = self.cellsQueue.get()
        logger.info(f"{len(cells)} cells found")

        self.imageWidget.markCells(cells)
        self.controlWidget.setCurrentIndex(1)


    def count(self):
        cells = getCells(self.imageWidget.fullImage)
        self.cellsQueue.put(cells)
        self.countingDoneSignal.emit()


    @pyqtSlot(str)
    def openErrorMessage(self, msg):
        logger.fatal(msg)
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setText(msg)
        msgBox.setWindowTitle("Error")
        msgBox.exec_()


    def saveImage(self, fileName = None):
        """save image to usb file. default file name is timestamp
        :param str fileName: ending .tiff is added automatically"""
        self.infoTextBox.setText("Saving image")
        self.page2Widget.setEnabled(False)
        try:
            usbPath = util.getUsbDevicePath()
        except IndexError:
            self.page2Widget.setEnabled(True)
            self.infoTextBox.setText("Saving failed")
            self.errorSignal.emit("No USB device found - file was not saved")
            return
        if fileName is None:
            fileName = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        cv2.imwrite(os.path.join(usbPath, fileName + ".tiff"), cv2.cvtColor(self.imageWidget.fullImage     , cv2.COLOR_RGB2BGR))
        if isinstance(self.imageWidget.annotatedImage, np.ndarray):
            cv2.imwrite(os.path.join(usbPath, fileName + "_annotated.tiff"), cv2.cvtColor(self.imageWidget.annotatedImage, cv2.COLOR_RGB2BGR))
        logger.info("Saved File to " + usbPath)
        self.page2Widget.setEnabled(True)
        self.infoTextBox.setText("Image saved")

"""Class to handle LEDs and camera."""
import time
import os
import threading
import subprocess
import cv2

import constants
from logger import logger

if os.uname().nodename == "raspberrypi":
    import RPi.GPIO as GPIO
    from rpi_ws281x import Adafruit_NeoPixel

    testMode = False
    logger.info("Running on pi!")
else:
    testMode = True
    logger.info("Running in test mode (not on pi)")



class HardwareHandler():
    """Class to handle LEDs and camera."""
    def __init__(self, imageQueue):

        self.imageQueue = imageQueue
        self.capture = False
        self.capture_thread = None
        self.cap = cv2.VideoCapture(constants.CAMERA_NUM-1 + cv2.CAP_ANY)

        self.UV_LED    = False
        self.COLOR_LED = False

        if not testMode:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(constants.GPIO_UV_LED   ,GPIO.OUT)
            self.UV_LED_PWM =  GPIO.PWM(constants.GPIO_UV_LED, 800)  # channel=12 frequency=50Hz
            self.UV_LED_PWM.start(0)


            self.strip = Adafruit_NeoPixel(constants.COLOR_LED_NUM, constants.GPIO_COLOR_LED, dma = 10)
            self.strip.begin()
            for n in range(constants.COLOR_LED_NUM):
                self.strip.setPixelColorRGB(n,
                                            constants.settings["Color"]["LED_Red"  ],
                                            constants.settings["Color"]["LED_Green"],
                                            constants.settings["Color"]["LED_Blue"])


###################### LED ######################

    def switchUV_LED(self, val = None):
        """ switch UV LED or set to val"""
        if val is not None:
            self.UV_LED = val
        else:
            self.UV_LED = not self.UV_LED
        if not testMode:
            if self.UV_LED:
                self.UV_LED_PWM.ChangeDutyCycle(constants.settings["UV"]["LED_Brigh"])
            else:
                self.UV_LED_PWM.ChangeDutyCycle(0)
        if    self.UV_LED: logger.info("UV LED: On")
        else:              logger.info("UV LED: Off")

    def switchCOLOR_LED(self, val = None):
        """ switch color LED or set to val
        :param bool val:"""
        if val is not None:
            self.COLOR_LED = val
        else:
            self.COLOR_LED = not self.COLOR_LED
        if not testMode:
            if self.COLOR_LED:
                self.strip.setBrightness(constants.settings["Color"]["LED_Brigh"])
            else:
                self.strip.setBrightness(0)
            self.strip.show()
        if self.COLOR_LED: logger.info("Color LED: On")
        else             : logger.info("Color LED: Off")


    def updateLEDColors(self):
        """ Update Color LED settings to constants.settings """
        if not testMode:
            for n in range(constants.COLOR_LED_NUM):
                self.strip.setPixelColorRGB(n,
                                            constants.settings["Color"]["LED_Red"  ],
                                            constants.settings["Color"]["LED_Green"],
                                            constants.settings["Color"]["LED_Blue"])
            if self.COLOR_LED:
                self.strip.setBrightness(constants.settings["Color"]["LED_Brigh"])
                self.strip.show()
        else:
            color = (constants.settings["Color"]["LED_Red"  ],
                     constants.settings["Color"]["LED_Green"],
                     constants.settings["Color"]["LED_Blue" ],
                     constants.settings["Color"]["LED_Brigh"])
            logger.info(f"New LED Color: {color}. LED on: {self.COLOR_LED}")

    def updateLEDUV(self):
        """ Update UV LED settings to constants.settings """
        if not testMode:
            if self.UV_LED:
                self.UV_LED_PWM.ChangeDutyCycle(constants.settings["UV"]["LED_Brigh"])
        else:
            logger.info(f"New UV LED Brightness: {constants.settings['UV']['LED_Brigh']}. LED on: {self.UV_LED}")


###################### Camera ######################

    def startCapturing(self, mode = "Color"):
        """ Start image capture & display """
        self.capture = True
        def grab_images(queue):
            self.setCaptureSettings(mode, "low")
            while self.capture:
                if self.cap.grab():
                    _ , image = self.cap.retrieve(0)
                    if image is not None and queue.qsize() < 2:
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        image = cv2.resize  (image, constants.DISPLAY_RESOLUTION[::-1], interpolation=cv2.INTER_CUBIC)
                        queue.put(image)
                    else:
                        time.sleep(constants.DISP_MSEC / 1000.0)
                else:
                    logger.fatal("Can't grab camera image")
                    logger.fatal("Using test image instead")
                    image = cv2.imread(constants.TEST_IMAGE_NAME)
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    image = cv2.resize  (image, constants.DISPLAY_RESOLUTION[::-1], interpolation=cv2.INTER_CUBIC)
                    queue.put(image)
                    break

        self.capture_thread = threading.Thread(target = grab_images, args   = (self.imageQueue,)) # Thread to grab images
        self.capture_thread.start()

    def shootImage_fullResolution(self, mode = "Color"):
        """Shoot single image with maximal camera resolution
        :return np.ndarray: image """
        self.setCaptureSettings(mode, "full")
        if self.cap.grab():
            _ , fullImage = self.cap.retrieve(0)
        else:
            logger.fatal("Can't grab camera image")
            logger.fatal("Using test image instead")
            fullImage = cv2.imread(constants.TEST_IMAGE_NAME)

        fullImage = cv2.cvtColor(fullImage, cv2.COLOR_RGB2BGR)

        return fullImage

    def stopCapturing(self):
        """Stop if capturing."""
        if self.capture:
            self.capture = False
            self.capture_thread.join()
        self.imageQueue.queue.clear()

    def updateCaptureSettings(self, mode = "Color"):
        """Stop capturing and start again with new settings"""
        self.stopCapturing()
        self.startCapturing(mode = mode)

    def __del__(self):
        if not testMode: GPIO.cleanup()

    def setCaptureSettings(self, LEDMmode, resolution):
        """Call cv2.VideoCapture and set settings."""

        #set fps dynamic to exposure
        fps = 20
        if constants.settings[LEDMmode]["exposureTime"] != 0:
            fps = int(max(1, min(20, 10000 / constants.settings[LEDMmode]["exposureTime"])))
        self.cap.set(cv2.CAP_PROP_FPS, fps)

        if resolution == "full":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH , constants.CAMERA_RESOLUTION[1])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, constants.CAMERA_RESOLUTION[0])
        if resolution == "low":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH , constants.DISPLAY_RESOLUTION[1])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, constants.DISPLAY_RESOLUTION[0])


        if not testMode:
            #set white balance
            subprocess.check_call(f"v4l2-ctl -d /dev/video0 -c white_balance_auto_preset=0 -c red_balance={constants.RED_GAIN} -c blue_balance={constants.BLUE_GAIN} -c exposure_dynamic_framerate=1 -c iso_sensitivity_auto=0 ", shell = True)
            #set exposure
            if constants.settings[LEDMmode]["exposureTime"] == 0: # exposureTime==0 -> auto
                subprocess.check_call("v4l2-ctl -d /dev/video0 -c white_balance_auto_preset=0 -c auto_exposure=0", shell = True)
            else:
                subprocess.check_call(f"v4l2-ctl -d /dev/video0 -c auto_exposure=1 -c exposure_time_absolute={constants.settings[LEDMmode]['exposureTime']}", shell = True)
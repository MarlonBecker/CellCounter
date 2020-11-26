import json
import os
from pathlib import Path
from PyQt5.QtCore import QObject, QEvent, pyqtSignal
from PyQt5.QtWidgets import QSlider

from getpass import getuser

from logger import logger
import constants


class ObjectResizer(QObject):
    """event filter to fix size of widget to parents size"""
    def __init__(self, parent, objToTesize):
        super(ObjectResizer, self).__init__(parent)
        self.objToTesize = objToTesize

    def eventFilter(self, obj: QObject, event: QEvent):
        if event.type() == QEvent.Resize:
            self.objToTesize.resize(obj.size())
        return False


class IntervalSlider(QSlider):
    """Slider with interval constrain."""
    _valueChanged = pyqtSignal(int)
    def __init__(self, *args, minValue = 0, maxValue = 100, interval = 1, **kwargs):
        super(IntervalSlider, self).__init__(*args, **kwargs)

        self._minValue = minValue
        self._maxValue = maxValue
        self._interval = interval
        self._adjustRange()

        self.valueChanged  = self._valueChanged

        super().valueChanged.connect(self.valueChangedSignal)

    def valueChangedSignal(self, val):
        self.valueChanged.emit(self._minValue + val * self._interval)

    def setMinimum(self, value):
        self._minValue = value
        self._adjustRange()

    def setMaximum(self, value):
        self._maxValue = value
        self._adjustRange()

    def setInterval(self, value):
        self._interval = value
        self._adjustRange()

    def _adjustRange(self):
        super(IntervalSlider, self).setMaximum(int((self._maxValue - self._minValue) / self._interval))

    def value(self):
        return self._minValue + super(IntervalSlider, self).value() * self._interval

    def setValue(self, value):
        super(IntervalSlider, self).setValue(int((value - self._minValue) / self._interval))



def loadSettings():
    """Parse resources/settings.json to constants.settings."""
    path = os.path.join(str(Path(__file__).parent.absolute()), "../resources/settings.json")
    if os.path.isfile( path ):
        with open(path) as file:
            try:
                constants.settings = json.load(file)
            except json.decoder.JSONDecodeError as e:
                logger.fatal("settings.json could not be parsed")
                constants.settings = {}
                raise e
    else:
        constants.settings = {}
        raise IOError("Settings file not found in resources/settings.json")

def saveSettings():
    """Save constants.settings to resources/settings.json"""
    path = os.path.join(str(Path(__file__).parent.absolute()), "../resources/settings.json")
    with open(path, "w") as file:
        json.dump(constants.settings, file, indent = 4)



def getUsbDevicePath():
    """Return first dir found in /media/ """
    user = getuser()
    dirs = list(os.walk(f"/media/"))
    return dirs[2][0]
    # return "./"

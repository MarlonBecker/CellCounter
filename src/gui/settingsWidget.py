"""Widget to set settings."""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QTabWidget, QCheckBox, QSlider

import constants

import util



class SettingsWidget(QWidget):
    """Widget to set settings. Capturing/LEDs are live updated"""
    UVLEDSettingsUpdatedSignal    = pyqtSignal()
    ColorLEDSettingsUpdatedSignal = pyqtSignal()
    showSettingsUpdatedSignal     = pyqtSignal()
    captureSettingsUpdatedSignal  = pyqtSignal(str)
    resetSignal                   = pyqtSignal()

    def __init__(self, parent = None):
        super(SettingsWidget, self).__init__(parent)


        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0,0,0,0)

        self.resetting = False #flag to avoid double emission of signals during reset. @TODO find better solution


        ################ buttons ################
        self.buttonsWidget = QWidget(self)
        self.buttonsLayout = QHBoxLayout(self.buttonsWidget)
        self.buttonsLayout.setContentsMargins(0,0,0,0)

        # reset button
        self.resetButton = QPushButton("&Reset")
        self.resetButton.clicked.connect(self.reset)

        # save as default button
        self.saveAsDefaultButton = QPushButton("&Save")
        self.saveAsDefaultButton.clicked.connect(util.saveSettings)

        #OK button
        self.OKButton = QPushButton("&OK")
        self.OKButton.setDefault(True)


        self.buttonsLayout.addWidget(self.saveAsDefaultButton)
        self.buttonsLayout.addWidget(self.resetButton)
        self.buttonsLayout.addWidget(self.OKButton)


        ###################### tabs ################
        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet(f"QTabWidget::tab-bar {{alignment: center;}} .QTabBar::tab {{height: 50px; width: {int(320/3)}px;}}")

        #######--------> Color <--------#######
        self.ColorTab = QWidget(self.tabs)
        self.tabs.addTab(self.ColorTab, "Color")
        self.ColorLayout = QGridLayout(self.ColorTab)

        # sliders and labels#
        self.ColorSliders = {}
        self.ColorLabels  = {}
        #### LED #####
        for i, name in enumerate(["Red", "Green", "Blue", "Brigh"]):
            slid  = QSlider(Qt.Vertical)

            slid.setMaximum(255)
            slid.setValue(constants.settings["Color"][f"LED_{name}"])
            slid.valueChanged.connect(self.updateLEDColors)

            label = QLabel(f"{name}\n{slid.value()}"  , alignment = Qt.AlignCenter)

            self.ColorLayout.addWidget(label, 0, i)
            self.ColorLayout.addWidget(slid , 1, i)

            self.ColorSliders[name] = slid
            self.ColorLabels [name] = label

        #### capture #####
        slid  = util.IntervalSlider(Qt.Vertical, maxValue = 1000, interval = 25)
        slid.setValue(constants.settings["Color"]["exposureTime"])
        label = QLabel(f"Exp\n{slid.value()}"  , alignment = Qt.AlignCenter)
        slid.valueChanged.connect(lambda val, label = label: label.setText(f"Exp\n{val}"))
        slid.sliderReleased.connect(lambda : self.updateExposure("Color"))

        self.ColorLayout.addWidget(label, 0, len(self.ColorSliders))
        self.ColorLayout.addWidget(slid , 1, len(self.ColorSliders))

        self.ColorSliders["Exp"] = slid
        self.ColorLabels ["Exp"] = label

        #######--------> UV <--------#######
        self.UVTab = QWidget(self.tabs)
        self.tabs.addTab(self.UVTab, "UV")
        self.UVLayout = QGridLayout(self.UVTab)

        # sliders and labels#
        self.UVSliders = {}
        self.UVLabels  = {}
        #### LED #####
        slid  = QSlider(Qt.Vertical)

        slid.setMaximum(100)
        slid.setValue(constants.settings["Color"]["LED_Brigh"])
        slid.valueChanged.connect(self.updateLEDUV)

        label = QLabel(f"Brigh\n{slid.value()}"  , alignment = Qt.AlignCenter)

        self.UVLayout.addWidget(label, 0, 0)
        self.UVLayout.addWidget(slid , 1, 0)

        self.UVSliders["Brigh"] = slid
        self.UVLabels ["Brigh"] = label

        #### capture #####
        slid  = util.IntervalSlider(Qt.Vertical, maxValue = 6000, interval = 100)
        slid.setValue(constants.settings["UV"]["exposureTime"])
        label = QLabel(f"Exp\n{slid.value()}"  , alignment = Qt.AlignCenter)
        slid.valueChanged.connect(lambda val, label = label: label.setText(f"Exp\n{val}"))
        slid.sliderReleased.connect(lambda : self.updateExposure("UV"))

        self.UVLayout.addWidget(label, 0, 1)
        self.UVLayout.addWidget(slid , 1, 1)

        self.UVSliders["Exp"] = slid
        self.UVLabels ["Exp"] = label

        #######--------> show <--------#######
        self.showTab = QWidget(self.tabs)
        self.tabs.addTab(self.showTab, "Show")
        self.showLayout = QVBoxLayout(self.showTab)

        self.showColorCheckboxes = {}
        for i, name in enumerate(["Red", "Green", "Blue"]):
            widget = QWidget(self.showTab)
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0,0,0,0)

            label = QLabel(f"Show {name}", widget)
            # label.setFixedWidth(150)
            layout.addWidget(label)

            checkbox = QCheckBox(widget)
            checkbox.setChecked(constants.settings["show"][name])
            checkbox.setStyleSheet("QCheckBox::indicator { width:50px; height: 50px;}")
            checkbox.stateChanged.connect(self.updateShow)
            layout.addWidget(checkbox)

            self.showLayout.addWidget(widget)
            self.showColorCheckboxes[name] = checkbox

        self.showLayout.addStretch()

        #@TODO move up
        self.mainLayout.addWidget(self.tabs)
        self.mainLayout.addWidget(self.buttonsWidget)



    def reset(self):
        """Reset settings."""
        util.loadSettings()

        # block signals while resetting gui buttons to avoid double emission of signals
        self.resetting = True
        # self.blockSignals(True)

        #reset slider, labels and checkboxes
        for name in ["Red", "Green", "Blue", "Brigh"]:
            self.ColorSliders[name].setValue(constants.settings["Color"][f"LED_{name}"])
            self.ColorLabels [name].setText(f"{name}\n{constants.settings['Color'][f'LED_{name}']}")
        self.ColorSliders["Exp"].setValue(constants.settings["Color"]["exposureTime"])
        self.ColorLabels ["Exp"].setText(f"Exp\n{constants.settings['Color']['exposureTime']}")

        self.UVSliders["Brigh"].setValue(constants.settings["UV"]["LED_Brigh"])
        self.UVLabels ["Brigh"].setText(f"Brigh\n{constants.settings['UV']['LED_Brigh']}")
        self.UVSliders["Exp"].setValue(constants.settings["UV"]["exposureTime"])
        self.UVLabels ["Exp"].setText(f"Exp\n{constants.settings['UV']['exposureTime']}")

        for name, checkbox in self.showColorCheckboxes.items():
            checkbox.setChecked(constants.settings["show"][name])

        # self.blockSignals(False)
        self.resetting = False
        self.resetSignal.emit()

    def updateLEDColors(self):
        if self.resetting: return
        for name in ["Red", "Green", "Blue", "Brigh"]:
            constants.settings["Color"][f"LED_{name}"] = self.ColorSliders[name].value()
            self.ColorLabels[name].setText(f"{name}\n{constants.settings['Color'][f'LED_{name}']}")
        self.ColorLEDSettingsUpdatedSignal.emit()

    def updateLEDUV(self):
        if self.resetting: return
        constants.settings["UV"]["LED_Brigh"] = self.UVSliders["Brigh"].value()
        self.UVLabels ["Brigh"].setText(f"Brigh\n{constants.settings['UV']['LED_Brigh']}")
        self.UVLEDSettingsUpdatedSignal.emit()

    def updateExposure(self, name):
        """:param str name: Color or UV """
        if self.resetting: return
        if   name == "Color":     constants.settings[name]["exposureTime"] = self.ColorSliders["Exp"].value()
        elif name == "UV":        constants.settings[name]["exposureTime"] = self.UVSliders   ["Exp"].value()
        self.captureSettingsUpdatedSignal.emit(name)

    def updateShow(self):
        """Show mode updated"""
        if self.resetting: return
        for name, checkbox in self.showColorCheckboxes.items():
            constants.settings["show"][name] = checkbox.isChecked()
        self.showSettingsUpdatedSignal.emit()

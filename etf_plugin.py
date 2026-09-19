# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from .etf_dialog import ExelToFeatureDialog


class AxelToFeatureETFPlugin(object):
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None
        self.dialog = None

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        self.action = QAction(
            icon,
            "Exel to Feature (Coordinate Transformation)",
            self.iface.mainWindow())
        self.action.setObjectName(
            "ExelToFeatureCoordinateTransformationAction")
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu("RUANG SPASIAL", self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginVectorMenu("RUANG SPASIAL", self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None

    def run(self):
        self.dialog = ExelToFeatureDialog(self.iface, self.iface.mainWindow())
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

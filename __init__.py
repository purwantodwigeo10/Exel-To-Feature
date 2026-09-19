# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later

def classFactory(iface):
    from .etf_plugin import AxelToFeatureETFPlugin
    return AxelToFeatureETFPlugin(iface)

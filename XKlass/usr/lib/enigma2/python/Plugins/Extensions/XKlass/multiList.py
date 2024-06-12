#!/usr/bin/python
# -*- coding: utf-8 -*-

from Components.GUIComponent import GUIComponent
from enigma import eListbox, eListboxPythonStringContent


class MultiList(GUIComponent):
    GUI_WIDGET = eListbox

    def __init__(self, menuList, enableWrapAround=None, content=eListboxPythonStringContent):
        GUIComponent.__init__(self)
        self.list = menuList
        self.l = content()
        self.l.setList(self.list)
        self.onSelectionChanged = []

    def postWidgetCreate(self, instance):
        instance.setContent(self.l)

    def preWidgetRemove(self, instance):
        instance.setContent(None)

    def setList(self, menuList):
        self.list = menuList
        self.l.setList(self.list)

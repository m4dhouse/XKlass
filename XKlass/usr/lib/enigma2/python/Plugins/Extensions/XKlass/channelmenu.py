#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _
from . import xklass_globals as glob
from .plugin import skin_directory, cfg, version
from .xStaticText import StaticText

from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Screens.Screen import Screen
from time import time
from Screens.MessageBox import MessageBox

import os

try:
    from http.client import HTTPConnection
    HTTPConnection.debuglevel = 0
except:
    from httplib import HTTPConnection
    HTTPConnection.debuglevel = 0


class XKlass_ChannelMenu(Screen):
    ALLOW_SUSPEND = True

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        skin_path = os.path.join(skin_directory, cfg.skin.value)

        skin = os.path.join(skin_path, "channelmenu.xml")
        with open(skin, "r") as f:
            self.skin = f.read()

        self.list = []
        self.drawList = []
        self.playlists_all = []
        self["list"] = List(self.drawList, enableWrapAround=True)

        self.setup_title = (_("Menu"))

        self["key_red"] = StaticText(_("Back"))
        self["key_green"] = StaticText(_("OK"))

        self['dialogactions'] = ActionMap(['XKlassActions'], {
            "green": self.__next__,
            "ok": self.__next__,
            "up": self.keyUp,
            "down": self.keyDown,
        }, -1)

        self["version"] = StaticText()
        self["version"].setText(version)

        self["dialogactions"].setEnabled(True)

        self.reload = "False"

        self.createSetup()

        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)

    def createSetup(self):
        self.list = []

        self.list.append([1, _("Live")])
        self.list.append([2, _("Vod")])
        self.list.append([3, _("Series")])
        self.list.append([4, _("Catchup")])
        self.list.append([5, _("Manual EPG Update")])
        self.list.append([6, _("Playlist Settings")])
        self.list.append([7, _("Show/Hide Channels")])
        self.list.append([8, _("Account Info")])
        self.list.append([9, _("Set As Default Playlist")])
        self.list.append([10, _("Switch Playlist")])
        self.list.append([11, _("Add New Playlist")])
        self.list.append([12, _("Download Manager")])
        self.list.append([13, _("Main Settings")])

        self.drawList = []
        self.drawList = [buildListEntry(x[0], x[1]) for x in self.list]
        self["list"].setList(self.drawList)

    def __next__(self):
        choice = self["list"].getCurrent()[1]

        if self["list"].getCurrent():
            if choice == "":
                pass

            if choice == _("Live"):
                self.showLive()
            if choice == _("Vod"):
                self.showVod()
            if choice == _("Series"):
                self.showSeries()
            if choice == _("Catchup"):
                self.showCatchup()
            if choice == _("Manual EPG Update"):
                self.manualEPGUpdate()
            if choice == _("Playlist Settings"):
                self.playlistSettings()
            if choice == _("Show/Hide Channels"):
                self.showHidden()
            if choice == _("Account Info"):
                self.userInfo()
            if choice == ("Set As Default Playlist"):
                self.defaultPlaylist()
            if choice == _("Switch Playlist"):
                self.showPlaylists()
            if choice == _("Add New Playlist"):
                self.addPlaylist()
            if choice == _("Download Manager"):
                self.downloadManager()
            if choice == _("Main Settings"):
                self.mainSettings()

    def showLive(self):
        pass

    def showVod(self):
        pass

    def showSeries(self):
        pass

    def showCatchup(self):
        pass

    def manualEPGUpdate(self):
        recordings = ""
        next_rec_time = -1

        try:
            recordings = glob.session.nav.getRecordings()
            if not recordings:
                next_rec_time = glob.session.nav.RecordTimer.getNextRecordingTime()
        except Exception as e:
            print(e)

        if recordings or (next_rec_time > 0 and (next_rec_time - time()) < 360):
            glob.session.open(MessageBox, _("Recordings in progress. EPG not downloaded."), type=MessageBox.TYPE_INFO, timeout=5)
        else:
            glob.session.openWithCallback(self.manualEPGUpdate2, MessageBox, _("EPGs downloading."), type=MessageBox.TYPE_INFO, timeout=5)

    def manualEPGUpdate2(self, data=None):
        from . import update
        update.XKlass_Update(glob.session, "manual")

    def playlistSettings(self):
        from . import playsettings
        glob.session.openWithCallback(self.callback, playsettings.XKlass_Settings)

    def showHidden(self):
        pass

    def userInfo(self):
        from . import serverinfo
        if "user_info" in glob.active_playlist:
            if "auth" in glob.active_playlist["user_info"]:
                if glob.active_playlist["user_info"]["auth"] == 1:
                    self.session.open(serverinfo.XKlass_UserInfo)

    def defaultPlaylist():
        pass

    def showPlaylists(self):
        pass

    def addPlaylist(self):
        pass

    def downloadManager(self):
        pass

    def mainSettings(self):
        pass

    def keyUp(self):
        self['list'].up()

    def keyDown(self):
        self['list'].down()

    def callback(self, answer=None):
        self.reload = "True"
        glob.ChoiceBoxDialog.show()


def buildListEntry(index, choice):
    icon = None

    if choice == _("Live"):
        icon = ""
    if choice == _("Vod"):
        icon = ""
    if choice == _("Series"):
        icon = ""
    if choice == _("Catchup"):
        icon = ""
    if choice == _("Manual EPG Update"):
        icon = ""
    if choice == _("Playlist Settings"):
        icon = ""
    if choice == _("Show/Hide Channels"):
        icon = ""
    if choice == _("Account Info"):
        icon = ""
    if choice == ("Set As Default Playlist"):
        icon = ""
    if choice == _("Switch Playlist"):
        icon = ""
    if choice == _("Add New Playlist"):
        icon = ""
    if choice == _("Download Manager"):
        icon = ""
    if choice == _("Main Settings"):
        icon = ""

    return (index, str(choice), icon)

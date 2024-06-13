#!/usr/bin/python
# -*- coding: utf-8 -*-

# Standard library imports
import os
import json
from time import time

try:
    from http.client import HTTPConnection
    HTTPConnection.debuglevel = 0
except:
    from httplib import HTTPConnection
    HTTPConnection.debuglevel = 0

# Enigma2 components
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

# Local application/library-specific imports
from . import _
from . import xklass_globals as glob
from .plugin import skin_directory, cfg, version, downloads_json
from .xStaticText import StaticText
from . import processfiles as loadfiles


class XKlass_ChannelMenu(Screen):
    ALLOW_SUSPEND = True

    instance = None

    def __init__(self, session, callfunc, previous_screen):
        Screen.__init__(self, session)
        self.session = session
        self.callfunc = callfunc
        self.previous_screen = previous_screen

        skin_path = os.path.join(skin_directory, cfg.skin.value)

        skin = os.path.join(skin_path, "channelmenu.xml")
        with open(skin, "r") as f:
            self.skin = f.read()

        self.list = []
        self.drawList = []
        self.playlists_all = self.playlists_all = loadfiles.process_files()
        self["list"] = List(self.drawList, enableWrapAround=True)

        self.setup_title = (_("Menu"))

        self.provider = glob.active_playlist["playlist_info"]["name"]
        self["provider"] = StaticText(self.provider)

        self["key_red"] = StaticText(_("Back"))
        self["key_green"] = StaticText(_("OK"))

        self['dialogactions'] = ActionMap(['XKlassActions'], {
            "green": self.__next__,
            "ok": self.__next__,
            "up": self.goUp,
            "down": self.goDown,
            "left": self.pageUp,
            "right": self.pageDown,
            "0": self.reset,
        }, -1)

        self["version"] = StaticText()
        self["version"].setText(version)

        self.createSetup()

        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)

    def goUp(self):
        instance = self["list"].master.master.instance
        instance.moveSelection(instance.moveUp)

    def goDown(self):
        instance = self["list"].master.master.instance
        instance.moveSelection(instance.moveDown)

    def pageUp(self):
        instance = self["list"].master.master.instance
        instance.moveSelection(instance.pageUp)

    def pageDown(self):
        instance = self["list"].master.master.instance
        instance.moveSelection(instance.pageDown)

    # button 0
    def reset(self):
        self["list"].setIndex(0)

    def createSetup(self):
        # print("*** createsetup **")
        self.provider = glob.active_playlist["playlist_info"]["name"]
        self["provider"].setText(self.provider)

        self.list = []
        """
        if glob.active_playlist["player_info"]["showlive"] and self.callfunc != "live":
            self.list.append([1, _("Live")])
        if glob.active_playlist["player_info"]["showvod"] and self.callfunc != "vod":
            self.list.append([2, _("Vod")])
        if glob.active_playlist["player_info"]["showseries"] and self.callfunc != "series":
            self.list.append([3, _("Series")])
        if glob.active_playlist["player_info"]["showcatchup"] and self.callfunc != "catchup":
            self.list.append([4, _("Catchup")])
            """
        if glob.active_playlist["player_info"]["showlive"] and self.callfunc == "live":
            self.list.append([5, _("Manual EPG Update")])
        self.list.append([6, _("Playlist Settings")])
        if glob.current_list:
            self.list.append([7, _("Show/Hide Channels")])
        self.list.append([8, _("Account Info")])
        if cfg.defaultplaylist.value != glob.active_playlist["playlist_info"]["name"]:
            self.list.append([9, _("Set As Default Playlist")])
        if len(self.playlists_all) > 1:
            self.list.append([10, _("Switch Playlist")])
        self.list.append([11, _("Add New Playlist")])

        downloads_all = []
        if os.path.isfile(downloads_json) and os.stat(downloads_json).st_size > 0:
            try:
                with open(downloads_json, "r") as f:
                    downloads_all = json.load(f)
            except Exception as e:
                print(e)

        if downloads_all:
            self.list.append([12, _("Download Manager")])
        self.list.append([13, _("Global Settings")])

        self.drawList = []
        self.drawList = [buildListEntry(x[0], x[1]) for x in self.list]
        self["list"].setList(self.drawList)

    def __next__(self):
        choice = self["list"].getCurrent()[1]

        if self["list"].getCurrent():
            if choice == "":
                pass

            """
            if choice == _("Live"):
                self.showLive()
            if choice == _("Vod"):
                self.showVod()
            if choice == _("Series"):
                self.showSeries()
            if choice == _("Catchup"):
                self.showCatchup()
                """
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
            if choice == _("Global Settings"):
                self.mainSettings()

    """
    def showLive(self):
        glob.previous_screen = self.previous_screen
        self.exitDialog()

        # from . import live
        # self.session.open(live.XKlass_Live_Categories, "menu")

    def showVod(self):
        glob.previous_screen = self.previous_screen
        self.exitDialog()
        return "vod"
        # from . import vod
        # self.session.open(vod.XKlass_Vod_Categories, "menu")

    def showSeries(self):
        glob.previous_screen = self.previous_screen
        self.exitDialog()
        return "series"
        # from . import series
        # self.session.open(series.XKlass_Series_Categories, "menu")

    def showCatchup(self):
        glob.previous_screen = self.previous_screen
        self.exitDialog()
        # from . import catchup
        # self.session.open(catchup.XKlass_Catchup_Categories, "menu")
        """

    def manualEPGUpdate(self):
        self.closeDialog()

        recordings = ""
        next_rec_time = -1

        try:
            recordings = self.session.nav.getRecordings()
            if not recordings:
                next_rec_time = self.session.nav.RecordTimer.getNextRecordingTime()
        except Exception as e:
            print(e)

        if recordings or (next_rec_time > 0 and (next_rec_time - time()) < 360):
            self.session.open(MessageBox, _("Recordings in progress. EPG not downloaded."), type=MessageBox.TYPE_INFO, timeout=5)
        else:
            self.session.openWithCallback(self.manualEPGUpdate2, MessageBox, _("EPGs downloading."), type=MessageBox.TYPE_INFO, timeout=5)

    def manualEPGUpdate2(self, data=None):
        from . import update
        update.XKlass_Update(self.session, "manual")
        self.callback()

    def playlistSettings(self):
        self.closeDialog()
        from . import playsettings
        self.session.openWithCallback(self.callback, playsettings.XKlass_Settings)

    def showHidden(self):
        self.closeDialog()
        from . import hidden
        self.session.openWithCallback(self.callback, hidden.XKlass_HiddenCategories, glob.current_screen, glob.current_list, glob.current_level)

    def userInfo(self):
        self.closeDialog()
        from . import serverinfo
        if "user_info" in glob.active_playlist:
            if "auth" in glob.active_playlist["user_info"]:
                if glob.active_playlist["user_info"]["auth"] == 1:
                    self.session.openWithCallback(self.callback, serverinfo.XKlass_UserInfo)

    def defaultPlaylist(self):
        self.closeDialog()
        cfg.defaultplaylist.setValue(str(glob.active_playlist["playlist_info"]["name"]))
        cfg.save()
        pass

    def showPlaylists(self):
        self.closeDialog()
        from . import playlists
        self.session.openWithCallback(self.exitDialog, playlists.XKlass_Playlists)

    def addPlaylist(self):
        self.closeDialog()
        from . import server
        self.session.openWithCallback(self.callback, server.XKlass_AddServer)

    def downloadManager(self):
        self.closeDialog()
        from . import downloadmanager
        self.session.openWithCallback(self.callback, downloadmanager.XKlass_DownloadManager)

    def mainSettings(self):
        self.closeDialog()
        from . import settings
        self.session.openWithCallback(self.callback, settings.XKlass_Settings)

    def callback(self, answer=None):
        self.createSetup()
        if glob.ChoiceBoxDialog:
            glob.ChoiceBoxDialog['dialogactions'].execBegin()
            glob.ChoiceBoxDialog.show()

    def closeDialog(self):
        if glob.ChoiceBoxDialog:
            glob.ChoiceBoxDialog.hide()
            glob.ChoiceBoxDialog['dialogactions'].execEnd()

    def exitDialog(self):
        if glob.ChoiceBoxDialog:
            glob.ChoiceBoxDialog.hide()
            glob.ChoiceBoxDialog['dialogactions'].execEnd()
            self.session.deleteDialog(glob.ChoiceBoxDialog)


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
    if choice == _("Global Settings"):
        icon = ""

    return (index, str(choice), icon)

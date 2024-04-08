#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _
from . import xclass_globals as glob
from .plugin import skin_directory, cfg
from .xStaticText import StaticText

from Components.Label import Label
from Components.ActionMap import ActionMap
from datetime import datetime
from Screens.Screen import Screen

import json
import os


class XClass_UserInfo(Screen):
    ALLOW_SUSPEND = True

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        skin_path = os.path.join(skin_directory, cfg.skin.value)
        skin = os.path.join(skin_path, "userinfo.xml")
        with open(skin, "r") as f:
            self.skin = f.read()

        self.setup_title = (_("User Information"))

        self["status"] = Label("")
        self["expiry"] = Label("")
        self["created"] = Label("")
        self["trial"] = Label("")
        self["activeconn"] = Label("")
        self["maxconn"] = Label("")
        self["formats"] = Label("")
        self["realurl"] = Label("")
        self["timezone"] = Label("")
        self["serveroffset"] = Label("")

        self["t_status"] = StaticText(_("Status:"))
        self["t_expiry"] = StaticText(_("Expiry Date:"))
        self["t_created"] = StaticText(_("Created At:"))
        self["t_trial"] = StaticText(_("Is Trial:"))
        self["t_activeconn"] = StaticText(_("Active Connections:"))
        self["t_maxconn"] = StaticText(_("Max Connections:"))
        self["t_formats"] = StaticText(_("Allowed Output Formats:"))
        self["t_realurl"] = StaticText(_("Real URL:"))
        self["t_timezone"] = StaticText(_("Timezone:"))
        self["t_serveroffset"] = StaticText(_("Server Offset:"))

        self["actions"] = ActionMap(["XClassActions"], {
            "ok": self.quit,
            "cancel": self.quit,
            "red": self.quit,
            "menu": self.quit}, -2)

        self["key_red"] = StaticText(_("Close"))

        self.onFirstExecBegin.append(self.createUserSetup)
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)

    def createUserSetup(self):
        if "status" in glob.current_playlist["user_info"]:
            if glob.current_playlist["user_info"]["status"] == "Active":
                status = (_("Active"))
            elif glob.current_playlist["user_info"]["status"] == "Banned":
                status = (_("Banned"))
            elif glob.current_playlist["user_info"]["status"] == "Disabled":
                status = (_("Disabled"))
            elif glob.current_playlist["user_info"]["status"] == "Expired":
                status = (_("Expired"))

            self["status"].setText(status)

        if "exp_date" in glob.current_playlist["user_info"]:
            try:
                self["expiry"].setText(str(datetime.fromtimestamp(int(glob.current_playlist["user_info"]["exp_date"])).strftime("%d-%m-%Y  %H:%M")))
            except:
                self["expiry"].setText("Null")

        if "created_at" in glob.current_playlist["user_info"]:
            try:
                self["created"].setText(str(datetime.fromtimestamp(int(glob.current_playlist["user_info"]["created_at"])).strftime("%d-%m-%Y  %H:%M")))
            except:
                self["created"].setText("Null")

        if "is_trial" in glob.current_playlist["user_info"]:
            self["trial"].setText(str(glob.current_playlist["user_info"]["is_trial"]))

        if "active_cons" in glob.current_playlist["user_info"]:
            self["activeconn"].setText(str(glob.current_playlist["user_info"]["active_cons"]))

        if "max_connections" in glob.current_playlist["user_info"]:
            self["maxconn"].setText(str(glob.current_playlist["user_info"]["max_connections"]))

        if "allowed_output_formats" in glob.current_playlist["user_info"]:
            self["formats"].setText(str(json.dumps(glob.current_playlist["user_info"]["allowed_output_formats"])).lstrip("[").rstrip("]"))

        if "url" in glob.current_playlist["server_info"]:
            self["realurl"].setText(str(glob.current_playlist["server_info"]["url"]))

        if "timezone" in glob.current_playlist["server_info"]:
            self["timezone"].setText(str(glob.current_playlist["server_info"]["timezone"]))

        if "serveroffset" in glob.current_playlist["player_info"]:
            self["serveroffset"].setText(str(glob.current_playlist["player_info"]["serveroffset"]))

    def quit(self):
        self.close()

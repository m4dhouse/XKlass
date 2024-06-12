#!/usr/bin/python
# -*- coding: utf-8 -*-

# Standard library imports
import json
import os

try:
    from http.client import HTTPConnection
    HTTPConnection.debuglevel = 0
except ImportError:
    from httplib import HTTPConnection
    HTTPConnection.debuglevel = 0

# Third-party imports
from requests.adapters import HTTPAdapter, Retry

# Enigma2 components
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from enigma import eServiceReference, iPlayableService
from Components.ServiceEventTracker import ServiceEventTracker

# Local application/library-specific imports
from . import _
from . import xklass_globals as glob
from . import processfiles as loadfiles
from .plugin import (cfg, downloads_json, hasConcurrent, hasMultiprocessing, playlists_json, pythonFull, skin_directory, version)
from .xStaticText import StaticText


hdr = {'User-Agent': str(cfg.useragent.value)}


class XKlass_MainMenu(Screen):
    ALLOW_SUSPEND = True

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        skin_path = os.path.join(skin_directory, cfg.skin.value)

        skin = os.path.join(skin_path, "startmenu.xml")
        with open(skin, "r") as f:
            self.skin = f.read()

        self.list = []
        self.drawList = []
        self["list"] = List(self.drawList, enableWrapAround=True)

        self["background"] = StaticText("")
        # self["background"].hide()

        self.setup_title = _("Main Menu")

        self["version"] = StaticText()

        self["actions"] = ActionMap(["XKlassActions"], {
            "red": self.quit,
            "green": self.__next__,
            "ok": self.__next__,
            "menu": self.__next__,
            "cancel": self.quit,
            "left": self["list"].up,
            "right": self["list"].down,
        }, -2)

        self["version"].setText(version)

        self.playlists_all = loadfiles.process_files()

        self.defaultplaylist = cfg.defaultplaylist.value
        self.lastcategory = cfg.lastcategory.value

        try:
            glob.currentPlayingServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
            glob.currentPlayingServiceRefString = self.session.nav.getCurrentlyPlayingServiceReference().toString()
            glob.newPlayingServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
            glob.newPlayingServiceRefString = glob.newPlayingServiceRef.toString()
        except:
            pass

        self.dialogstack = self.session.dialog_stack
        self.summarystack = self.session.summary_stack

        if self.playlists_all:
            if self.defaultplaylist:
                p = 0
                for playlist in self.playlists_all:
                    if str(playlist["playlist_info"]["name"]) == self.defaultplaylist:
                        glob.active_playlist = playlist
                        glob.current_selection = p
                        break
                    p += 1
            else:
                cfg.defaultplaylist.setValue(str(self.playlists_all[0]["playlist_info"]["name"]))
                cfg.save()
                glob.active_playlist = self.playlists_all[0]
                glob.current_selection = 0

            self.player_api = glob.active_playlist["playlist_info"]["player_api"]

            self.p_live_categories_url = str(self.player_api) + "&action=get_live_categories"
            self.p_vod_categories_url = str(self.player_api) + "&action=get_vod_categories"
            self.p_series_categories_url = str(self.player_api) + "&action=get_series_categories"
            self.p_live_streams_url = str(self.player_api) + "&action=get_live_streams"

            glob.active_playlist["data"]["live_streams"] = []

            if cfg.introvideo.value:
                self.onShow.append(self.playVideo)
                self.tracker = ServiceEventTracker(screen=self, eventmap={
                    iPlayableService.evEOF: self.onEOF
                })
            else:
                self["background"].setText("True")

            self.onShow.append(self.createSetup)

        self.onLayoutFinish.append(self.__layoutFinished)
        self.onFirstExecBegin.append(self.check_dependencies)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)

    def refreshVariables(self):
        try:
            glob.currentPlayingServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
            glob.currentPlayingServiceRefString = self.session.nav.getCurrentlyPlayingServiceReference().toString()
            glob.newPlayingServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
            glob.newPlayingServiceRefString = glob.newPlayingServiceRef.toString()
        except:
            pass

        self.player_api = glob.active_playlist["playlist_info"]["player_api"]

        self.p_live_categories_url = str(self.player_api) + "&action=get_live_categories"
        self.p_vod_categories_url = str(self.player_api) + "&action=get_vod_categories"
        self.p_series_categories_url = str(self.player_api) + "&action=get_series_categories"
        self.p_live_streams_url = str(self.player_api) + "&action=get_live_streams"

        glob.active_playlist["data"]["live_streams"] = []

        self.start()

    def check_dependencies(self):
        print("*** self.session.summary ***", self.session.summary)
        print("**** self.session.dialog_stack ***", self.session.dialog_stack)
        print("**** self.session.summary_stack ***", self.session.summary_stack)
        try:
            if cfg.location_valid.value is False:
                self.session.open(MessageBox, _("Playlists.txt location is invalid and has been reset."), type=MessageBox.TYPE_INFO, timeout=5)
                cfg.location_valid.setValue(True)
                cfg.save()
        except:
            pass

        dependencies = True

        try:
            import requests
            from PIL import Image
            print("***** python version *** %s" % pythonFull)
            if pythonFull < 3.9:
                print("*** checking multiprocessing ***")
                from multiprocessing.pool import ThreadPool
        except Exception as e:
            print("**** missing dependencies ***")
            print(e)
            dependencies = False

        if dependencies is False:
            os.chmod("/usr/lib/enigma2/python/Plugins/Extensions/XKlass/dependencies.sh", 0o0755)
            cmd1 = ". /usr/lib/enigma2/python/Plugins/Extensions/XKlass/dependencies.sh"
            self.session.openWithCallback(self.start, Console, title="Checking Python Dependencies", cmdlist=[cmd1], closeOnSuccess=False)
        else:
            self.start()

    def start(self, answer=None):
        if not self.playlists_all:
            self.addServer()
            self.close()
        else:
            self.makeUrlList()

    def addServer(self):
        from . import server
        self.session.openWithCallback(self.quit, server.XKlass_AddServer)

    def makeUrlList(self):
        self.url_list = []

        player_api = str(glob.active_playlist["playlist_info"].get("player_api", ""))
        full_url = str(glob.active_playlist["playlist_info"].get("full_url", ""))
        domain = str(glob.active_playlist["playlist_info"].get("domain", ""))
        username = str(glob.active_playlist["playlist_info"].get("username", ""))
        password = str(glob.active_playlist["playlist_info"].get("password", ""))
        if "get.php" in full_url and domain and username and password:
            self.url_list.append([player_api, 0])
            self.url_list.append([self.p_live_categories_url, 1])
            self.url_list.append([self.p_vod_categories_url, 2])
            self.url_list.append([self.p_series_categories_url, 3])

            if glob.active_playlist["data"]["data_downloaded"] is False:
                self.url_list.append([self.p_live_streams_url, 4])

        self.process_downloads()

    def download_url(self, url):
        import requests
        index = url[1]
        response = ""

        retries = Retry(total=2, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retries)

        with requests.Session() as http:
            http.mount("http://", adapter)
            http.mount("https://", adapter)

            try:
                r = http.get(url[0], headers=hdr, timeout=(6, 10), verify=False)
                r.raise_for_status()

                if r.status_code == requests.codes.ok:
                    try:
                        response = r.json()
                    except ValueError as e:
                        print("Error decoding JSON:", e, url)

            except Exception as e:
                print("Request error:", e)

        return index, response

    def process_downloads(self):
        threads = min(len(self.url_list), 10)

        self.retry = 0
        glob.active_playlist["data"]["live_categories"] = []
        glob.active_playlist["data"]["vod_categories"] = []
        glob.active_playlist["data"]["series_categories"] = []

        if hasConcurrent or hasMultiprocessing:
            if hasConcurrent:
                try:
                    from concurrent.futures import ThreadPoolExecutor
                    with ThreadPoolExecutor(max_workers=threads) as executor:
                        results = list(executor.map(self.download_url, self.url_list))
                except Exception as e:
                    print("Concurrent execution error:", e)

            elif hasMultiprocessing:
                try:
                    from multiprocessing.pool import ThreadPool
                    pool = ThreadPool(threads)
                    results = pool.imap_unordered(self.download_url, self.url_list)
                    pool.close()
                    pool.join()
                except Exception as e:
                    print("Multiprocessing execution error:", e)

            for index, response in results:
                if response:
                    if index == 0:
                        if "user_info" in response:
                            glob.active_playlist.update(response)
                        else:
                            glob.active_playlist["user_info"] = {}
                    if index == 1:
                        glob.active_playlist["data"]["live_categories"] = response
                    if index == 2:
                        glob.active_playlist["data"]["vod_categories"] = response
                    if index == 3:
                        glob.active_playlist["data"]["series_categories"] = response
                    if index == 4:
                        glob.active_playlist["data"]["live_streams"] = response
        else:
            # print("*** trying sequential ***")
            for url in self.url_list:
                result = self.download_url(url)
                index = result[0]
                response = result[1]
                if response:
                    if index == 0:
                        if "user_info" in response:
                            glob.active_playlist.update(response)
                        else:
                            glob.active_playlist["user_info"] = {}
                    if index == 1:
                        glob.active_playlist["data"]["live_categories"] = response
                    if index == 2:
                        glob.active_playlist["data"]["vod_categories"] = response
                    if index == 3:
                        glob.active_playlist["data"]["series_categories"] = response
                    if index == 4:
                        glob.active_playlist["data"]["live_streams"] = response

        glob.active_playlist["data"]["data_downloaded"] = True
        self.createSetup()

    def createSetup(self):
        def add_category_to_list(title, category_type, index):
            if category_type in glob.active_playlist["data"] and glob.active_playlist["data"][category_type]:
                if "category_id" in glob.active_playlist["data"][category_type][0] and "user_info" not in glob.active_playlist["data"][category_type]:
                    self.index += 1
                    self.list.append([self.index, _(title), index])

        self.list = []
        self.index = 0
        downloads_all = []
        if os.path.isfile(downloads_json) and os.stat(downloads_json).st_size > 0:
            try:
                with open(downloads_json, "r") as f:
                    downloads_all = json.load(f)
            except Exception as e:
                print(e)

        show_live = glob.active_playlist["player_info"].get("showlive", False)
        show_vod = glob.active_playlist["player_info"].get("showvod", False)
        show_series = glob.active_playlist["player_info"].get("showseries", False)
        show_catchup = glob.active_playlist["player_info"].get("showcatchup", False)

        content = glob.active_playlist["data"]["live_streams"]

        has_catchup = any(str(item.get("tv_archive", "0")) == "1" for item in content if "tv_archive" in item)
        has_custom_sids = any(item.get("custom_sid", False) for item in content if "custom_sid" in item)

        glob.active_playlist["data"]["live_streams"] = []

        if has_custom_sids:
            glob.active_playlist["data"]["customsids"] = True

        if has_catchup:
            glob.active_playlist["data"]["catchup"] = True

        if show_live:
            add_category_to_list("Live TV", "live_categories", 0)

        if show_vod:
            add_category_to_list("Movies", "vod_categories", 1)

        if show_series:
            add_category_to_list("Series", "series_categories", 2)

        if show_catchup and glob.active_playlist["data"]["catchup"]:
            self.index += 1
            self.list.append([self.index, _("Catch Up TV"), 3])

        self.list.append([self.index, _("Global Settings"), 4])
        self.index += 1

        if downloads_all:
            self.index += 1
            self.list.append([self.index, _("Download Manager"), 5])

        self.drawList = [buildListEntry(x[0], x[1], x[2]) for x in self.list]
        self["list"].setList(self.drawList)

        self.writeJsonFile()

    def writeJsonFile(self):
        with open(playlists_json, "r") as f:
            playlists_all = json.load(f)

        playlists_all[glob.current_selection] = glob.active_playlist

        with open(playlists_json, "w") as f:
            json.dump(playlists_all, f)

    def __next__(self):
        self.stopVideo()

        current_entry = self["list"].getCurrent()

        if current_entry:
            index = current_entry[2]
            if index == 0:
                self.showLive()
            elif index == 1:
                self.showVod()
            elif index == 2:
                self.showSeries()
            elif index == 3:
                self.showCatchup()
            elif index == 4:
                self.mainSettings()
            elif index == 5:
                self.downloadManager()

    def showLive(self):
        from . import live
        self.session.openWithCallback(self.playVideo, live.XKlass_Live_Categories, "start")

    def showVod(self):
        from . import vod
        self.session.openWithCallback(self.playVideo, vod.XKlass_Vod_Categories, "start")

    def showSeries(self):
        from . import series
        self.session.openWithCallback(self.playVideo, series.XKlass_Series_Categories, "start")

    def showCatchup(self):
        from . import catchup
        self.session.openWithCallback(self.playVideo, catchup.XKlass_Catchup_Categories, "start")

    def mainSettings(self):
        from . import settings
        self.session.open(settings.XKlass_Settings)

    def downloadManager(self):
        from . import downloadManager
        self.session.open(downloadManager.XKlass_DownloadManager)

    def quit(self, data=None):
        self.playOriginalChannel()

    def playOriginalChannel(self):
        try:
            if glob.currentPlayingServiceRefString:
                self.session.nav.playService(eServiceReference(glob.currentPlayingServiceRefString))
        except Exception as e:
            print(e)

        self.close()

    def popSummary(self):
        if self.summary is not None:
            self.summary.doClose()
        if not self.summary_stack:
            self.summary = None
        else:
            self.summary = self.summary_stack.pop()
        if self.summary is not None:
            self.summary.show()

    def stopVideo(self):
        try:
            self.session.nav.stopService()
        except:
            pass

    def playVideo(self, result=None):
        self["background"].setText("")
        self.local_video_path = "/usr/lib/enigma2/python/Plugins/Extensions/XKlass/video/pixel-galaxy-576p.mp4"
        service = eServiceReference(4097, 0, self.local_video_path)
        self.session.nav.playService(service)

    def onEOF(self):
        # print("*** end of file ***")
        self["background"].setText("True")

        """
        service = self.session.nav.getCurrentService()
        seek = service and service.seek()
        if seek:
            seek.seekTo(0)
            """


def buildListEntry(index, title, num):
    return index, str(title), num

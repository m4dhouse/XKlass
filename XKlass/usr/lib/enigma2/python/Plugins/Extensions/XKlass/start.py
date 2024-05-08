#!/usr/bin/python
# -*- coding: utf-8 -*-


from . import _
from . import xklass_globals as glob
from . import processfiles as loadfiles
from .plugin import pythonFull, cfg, hdr, hasConcurrent, hasMultiprocessing

from enigma import eServiceReference
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from requests.adapters import HTTPAdapter, Retry

import os

try:
    from http.client import HTTPConnection
    HTTPConnection.debuglevel = 0
except:
    from httplib import HTTPConnection
    HTTPConnection.debuglevel = 0


class XKlass_Start(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        self.playlists_all = loadfiles.process_files()

        self.defaultplaylist = cfg.defaultplaylist.value
        self.lastcategory = cfg.lastcategory.value

        if self.playlists_all:
            if self.defaultplaylist:
                for playlist in self.playlists_all:
                    if str(playlist["playlist_info"]["name"]) == self.defaultplaylist:
                        glob.active_playlist = playlist
                        break
            else:
                glob.active_playlist = self.playlists_all[0]

            if self.session.nav.getCurrentlyPlayingServiceReference():
                glob.currentPlayingServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
                glob.currentPlayingServiceRefString = self.session.nav.getCurrentlyPlayingServiceReference().toString()
                glob.newPlayingServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
                glob.newPlayingServiceRefString = glob.newPlayingServiceRef.toString()

            self.player_api = glob.active_playlist["playlist_info"]["player_api"]

            self.p_live_categories_url = str(self.player_api) + "&action=get_live_categories"
            self.p_vod_categories_url = str(self.player_api) + "&action=get_vod_categories"
            self.p_series_categories_url = str(self.player_api) + "&action=get_series_categories"
            self.p_live_streams_url = str(self.player_api) + "&action=get_live_streams"

            glob.active_playlist["data"]["live_streams"] = []

        self.onFirstExecBegin.append(self.check_dependencies)

    def check_dependencies(self):

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
        else:
            # check if default playlist set
            self.makeUrlList()

    def addServer(self):
        from . import server
        self.session.openWithCallback(self.exit, server.XKlass_AddServer)

    def exit(self, data=None):
        self.playOriginalChannel()

    def playOriginalChannel(self):
        if glob.currentPlayingServiceRefString != glob.newPlayingServiceRefString:
            if glob.newPlayingServiceRefString and glob.currentPlayingServiceRefString:
                self.session.nav.playService(eServiceReference(glob.currentPlayingServiceRefString))
        self.close()

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
                print("******* trying concurrent futures ******")
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

        # self["splash"].hide()
        glob.active_playlist["data"]["data_downloaded"] = True
        self.openCategories()

    def openCategories(self):
        if self.lastcategory:
            if self.lastcategory == "live":
                from . import live
                self.session.openWithCallback(self.exit, live.XKlass_Categories)
            elif self.lastcategory == "vod":
                from . import vod
                self.session.openWithCallback(self.exit, vod.XKlass_Categories)
            elif self.lastcategory == "series":
                from . import series
                self.session.openWithCallback(self.exit, series.XKlass_Categories)
            elif self.lastcategory == "catchup":
                from . import catchup
                self.session.openWithCallback(self.exit, catchup.XKlass_Categories)
        else:
            from . import live
            self.session.openWithCallback(self.exit, live.XKlass_Categories)

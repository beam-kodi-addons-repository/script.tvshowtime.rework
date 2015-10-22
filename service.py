import os,sys
import xbmc, xbmcaddon
import time

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

__addon__         = xbmcaddon.Addon()
__cwd__           = __addon__.getAddonInfo('path')
__scriptname__    = __addon__.getAddonInfo('name')
__version__       = __addon__.getAddonInfo('version')
__language__      = __addon__.getLocalizedString
__resource_path__ = os.path.join(__cwd__, 'resources', 'lib')
__resource__      = xbmc.translatePath(__resource_path__).decode('utf-8')

sys.path.append (__resource__)

from utilities import log, get_episode_info, set_episode_watched_status,reload_addon
from TVShowTimeClient import TVShowTimeClient

tvshowtime_client = TVShowTimeClient(__addon__.getSetting('access_token'))

class KodiMonitor(xbmc.Monitor):

    def onSettingsChanged(self):
        global __addon__
        __addon__ = xbmcaddon.Addon()
        reload_addon()

    def onNotification(self, sender, method, data):
        if method == "VideoLibrary.OnUpdate" or method == 'Player.OnStop':
            log([method,data])
            parsed_data = json.loads(data)
            if parsed_data['item']['type'] == 'episode':
                if method == 'Player.OnStop' and parsed_data['end'] == True:
                    set_episode_watched_status(tvshowtime_client,parsed_data['item']['id'], True)
                elif method == 'Player.OnStop' and parsed_data['end'] == False and __addon__.getSetting('send_status_on_every_player_stop') == 'true':
                    sleep_time = int(__addon__.getSetting('every_player_stop_sleep_time'))
                    log("Sleeping time before library reading.. %ss" % sleep_time)
                    time.sleep(sleep_time)
                    set_episode_watched_status(tvshowtime_client,parsed_data['item']['id'], None)
                elif method == "VideoLibrary.OnUpdate":
                    set_as_watched  = True if ('playcount' in parsed_data.keys() and parsed_data['playcount'] > 0) else None
                    set_episode_watched_status(tvshowtime_client,parsed_data['item']['id'], set_as_watched)


if (__name__ == "__main__"):
    log("Starting.. " + __version__)
    monitor = KodiMonitor()
    while not monitor.abortRequested():
	    if monitor.waitForAbort(10): break
    del monitor
    log("Stopped.. " + __version__)

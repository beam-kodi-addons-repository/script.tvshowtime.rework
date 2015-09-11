import os
import xbmc, xbmcaddon, xbmcgui
import time
import json

__addon__         = xbmcaddon.Addon()
__cwd__           = __addon__.getAddonInfo('path')
__scriptname__    = __addon__.getAddonInfo('name')
__version__       = __addon__.getAddonInfo('version')
__language__      = __addon__.getLocalizedString
__resource_path__ = os.path.join(__cwd__, 'resources', 'lib')
__resource__      = xbmc.translatePath(__resource_path__).decode('utf-8')

sys.path.append (__resource__)

from utilities import log, get_episode_info
from TVShowTimeClient import TVShowTimeClient

__access_token__  = __addon__.getSetting('access_token')
tvshowtime_client = TVShowTimeClient(__access_token__)

def app_start():
	global __access_token__

	menu_items = []
	if __access_token__ == '' or __access_token__ is None:
		__access_token__ = None
		menu_items.append("Login")
	else:
		menu_items.append("Sync")
		menu_items.append("Logout")

	xbmc_menu = xbmcgui.Dialog().select(__scriptname__, menu_items)
	log("Menu: " + str(xbmc_menu))

	if xbmc_menu == 0 and __access_token__ is None:
		progress = xbmcgui.DialogProgress()
		progress.create(__scriptname__, "Requesting code..")
		get_code = tvshowtime_client.get_code()
		progress.update(0,'Go to ' + get_code['verification_url'], 'Enter code: ' + get_code['user_code'])
		for auth_code in tvshowtime_client.wait_for_authorize(get_code):
			if progress.iscanceled(): break
		__addon__.setSetting('access_token', tvshowtime_client.get_authorization(auth_code))
	elif xbmc_menu == 0 and __access_token__ is not None:
		log("Sync")
	elif xbmc_menu == 1:
		__addon__.setSetting('access_token', None)
	else:
		return


app_start()

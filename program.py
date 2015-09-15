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

from utilities import log, get_episode_info, list_all_tv_shows, set_tvshow_follow_status, set_watched_episodes_of_tvshow
from TVShowTimeClient import TVShowTimeClient

tvshowtime_client = TVShowTimeClient(__addon__.getSetting('access_token'))

def app_start():
	menu_items = []
	if tvshowtime_client.is_token_empty():
		menu_items.append("Login")
	else:
		menu_items.append("Follow all Kodi shows on TVShowTime.com")
		menu_items.append("Mark watched episodes on TVShowTime.com")
		menu_items.append("Logout")

	xbmc_menu = xbmcgui.Dialog().select(__scriptname__, menu_items)

	if xbmc_menu == 0 and tvshowtime_client.is_token_empty():
		progress = xbmcgui.DialogProgress()
		progress.create(__scriptname__, "Requesting code..")
		get_code = tvshowtime_client.get_code()
		progress.update(0,'Go to ' + get_code['verification_url'], 'Enter code: ' + get_code['user_code'])
		for auth_code in tvshowtime_client.wait_for_authorize(get_code):
			if progress.iscanceled(): break
		__addon__.setSetting('access_token', tvshowtime_client.get_authorization(auth_code))
	elif xbmc_menu == 0 and not tvshowtime_client.is_token_empty():
		progress = xbmcgui.DialogProgressBG()
		progress.create(__scriptname__,"Starting tvshows sync..")
		for tvshow in list_all_tv_shows():
			percents = ((tvshow[1]*100)/tvshow[0])
			progress.update(percents,__scriptname__,tvshow[2]['label']) # imdbnumber
			set_tvshow_follow_status(tvshowtime_client,tvshow[2]['imdbnumber'],True,progress,percents)
			log(tvshow)
		progress.close()
	elif xbmc_menu == 1 and not tvshowtime_client.is_token_empty():
		log("Sync episodes")
		menu_items = []
		menu_items.append('All tvshows')
		all_tv_shows = list(list_all_tv_shows())
		for tvshow in list_all_tv_shows():
			menu_items.append(tvshow[2]['label'])
		xbmc_menu = xbmcgui.Dialog().select(__scriptname__, menu_items)
		progress = xbmcgui.DialogProgressBG()
		progress.create(__scriptname__,"Starting tvshows sync..")
		if xbmc_menu == 0:
			for tvshow in all_tv_shows:
				log(tvshow)
				set_watched_episodes_of_tvshow(tvshowtime_client, tvshow[2]['tvshowid'], tvshow[2]['imdbnumber'], progress, 0)	
			log("All shows")
		elif xbmc_menu == -1:
			log("Dialog cancelled")
			return
		else:
			tvshow = all_tv_shows[xbmc_menu-1]
			log(tvshow)
			set_watched_episodes_of_tvshow(tvshowtime_client, tvshow[2]['tvshowid'], tvshow[2]['imdbnumber'], progress, 0)
		progress.close()
	elif xbmc_menu == 2:
		__addon__.setSetting('access_token', None)
	else:
		return


app_start()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xbmc, xbmcaddon, xbmcgui
import json

__addon__         = xbmcaddon.Addon()
__scriptname__    = __addon__.getAddonInfo('name')

def log(message):
	xbmc.log("### " + __scriptname__ + ": " + str(message), level=xbmc.LOGNOTICE)

def get_episode_info(episode_id):
    rpccmd = {
    	'jsonrpc': '2.0', 
    	'method': 'VideoLibrary.GetEpisodeDetails', 
    	'params': { 'episodeid' : episode_id, 'properties' : ['uniqueid','playcount','tvshowid','showtitle','season','episode'] },
    	'id': 1
    }
    rpccmd = json.dumps(rpccmd)
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    return {
    	'play_count'      : result['result']['episodedetails']['playcount'],
    	'episode_tvdb_id' : result['result']['episodedetails']['uniqueid']['unknown'],
    	'tvshow_id'       : result['result']['episodedetails']['tvshowid'],
    	'tvshow_name'     : result['result']['episodedetails']['showtitle'],
    	'season'          : result['result']['episodedetails']['season'],
    	'episode'         : result['result']['episodedetails']['episode']
    }


def list_all_tv_shows():
    rpccmd = {
    	'jsonrpc': '2.0',
    	'method': 'VideoLibrary.GetTVShows',
    	'params': { 'properties' : ['imdbnumber'] },
    	'id': 1
    }
    rpccmd = json.dumps(rpccmd)
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    index = 0
    for tvshow in result['result']['tvshows']:
    	index += 1
    	yield [result['result']['limits']['total'],index,tvshow]

def wait_for_request(tvshowtime_client, progress = None, percent = None):
	for wait_time in tvshowtime_client.wait_for_available_request():
		status = "Waiting for available request.. " + str(wait_time) + "s"
		log(status)
		if progress is not None: progress.update(percent,__scriptname__,status)


def set_tvshow_follow_status(tvshowtime_client, tvshow_id, follow_status, progress = None, percent = None):
	if tvshowtime_client.is_token_empty():
		tvshowtime_client.token = __addon__.getSetting('access_token')

	if tvshowtime_client.is_authorized():
		wait_for_request(tvshowtime_client, progress, percent)
		tvshowtime_client.follow_show(tvshow_id,follow_status)

def set_episode_watched_status(tvshowtime_client, episode_id, progress = None, percent = None):
	if tvshowtime_client.is_token_empty():
		tvshowtime_client.token = __addon__.getSetting('access_token')

	tvdb_data = get_episode_info(episode_id)
	if tvshowtime_client.is_authorized():
		log(str(tvdb_data))
		wait_for_request(tvshowtime_client, progress, percent)
		tvshowtime_client.mark_episode(tvdb_data['episode_tvdb_id'],tvdb_data['play_count'] > 0)

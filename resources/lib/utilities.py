#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xbmc, xbmcaddon
import json

__addon__         = xbmcaddon.Addon()
__scriptname__    = __addon__.getAddonInfo('name')

def log(message):
	xbmc.log("### " + __scriptname__ + ": " + str(message), level=xbmc.LOGDEBUG)

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

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xbmc, xbmcaddon
import json

__addon__         = xbmcaddon.Addon()
__scriptname__    = __addon__.getAddonInfo('name')

def log(message):
	xbmc.log("### " + __scriptname__ + ": " + message, level=xbmc.LOGDEBUG)

def tvdb_id_and_played_from_episode_id(episode_id):
    rpccmd = {
    	'jsonrpc': '2.0', 
    	'method': 'VideoLibrary.GetEpisodeDetails', 
    	'params': { 'episodeid' : episode_id, 'properties' : ['uniqueid','playcount'] },
    	'id': 1
    }
    rpccmd = json.dumps(rpccmd)
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    return {
    	'playcount' : result['result']['episodedetails']['playcount'], 
    	'tvdb_id'	: result['result']['episodedetails']['uniqueid']['unknown']
    }

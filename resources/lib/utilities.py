#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xbmc, xbmcaddon, xbmcgui
import json, time

__addon__         = xbmcaddon.Addon()
__scriptname__    = __addon__.getAddonInfo('name')

def log(message):
    xbmc.log("### " + __scriptname__ + ": " + str(message), level=xbmc.LOGNOTICE)

def get_tvshow_episodes_watched_status(tvshow_id):
    rpccmd = {
        'jsonrpc': '2.0',
        'method' : 'VideoLibrary.GetEpisodes',
        'params': {
            'tvshowid' : int(tvshow_id),
            'properties' : ['playcount','season','episode'],
        },
        'id' : 1
    }
    result = execute_rpc_command(rpccmd)
    if result == None: return None
    return_result = {}
    for episode in result['result']['episodes']:
        if not int(episode['season']) in return_result.keys(): return_result[int(episode['season'])] = {}
        return_result[int(episode['season'])][int(episode['episode'])] = episode['playcount'] > 0
    return return_result

def check_watched_status_in_kodi(info_data, season_number, episode_number):
    if int(season_number) in info_data.keys():
        if int(episode_number) in info_data[int(season_number)].keys():
            return info_data[int(season_number)][int(episode_number)]
        else:
            return False
    else:
        return False

def get_episode_info(episode_id):
    rpccmd = {
        'jsonrpc': '2.0',
        'method': 'VideoLibrary.GetEpisodeDetails',
        'params': { 'episodeid' : episode_id, 'properties' : ['uniqueid','playcount','tvshowid','showtitle','season','episode'] },
        'id': 1
    }
    result = execute_rpc_command(rpccmd)
    if result == None: return None
    return {
        'id'              : result['result']['episodedetails']['id'],
        'play_count'      : result['result']['episodedetails']['playcount'],
        'episode_tvdb_id' : result['result']['episodedetails']['uniqueid']['unknown'],
        'tvshow_id'       : result['result']['episodedetails']['tvshowid'],
        'tvshow_name'     : result['result']['episodedetails']['showtitle'],
        'season'          : result['result']['episodedetails']['season'],
        'episode'         : result['result']['episodedetails']['episode'],
        'watched'         : result['result']['episodedetails']['playcount'] > 0
    }

def execute_rpc_command(rpccmd):
    rpccmd = json.dumps(rpccmd)
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    if 'error' in result.keys(): return None
    return result

def list_all_tv_shows():
    rpccmd = {
        'jsonrpc': '2.0',
        'method': 'VideoLibrary.GetTVShows',
        'params': { 
            'properties' : ['imdbnumber'], 
            'sort' : { 'order': 'ascending', 'method': 'label' } 
        },
        'id': 1
    }
    result = execute_rpc_command(rpccmd)
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

def set_episode_watched_status(tvshowtime_client, episode_id, watched_state = None ,progress = None, percent = None):
    if tvshowtime_client.is_token_empty():
        tvshowtime_client.token = __addon__.getSetting('access_token')

    tvdb_data = get_episode_info(episode_id)
    log(str(tvdb_data))

    if watched_state == None: watched_state = tvdb_data['watched']

    send_episode_watched_status(tvshowtime_client,tvdb_data['episode_tvdb_id'],watched_state,progress,percent)

def send_episode_watched_status(tvshowtime_client, tvdb_episode_id, watched_state = None ,progress = None, percent = None):
    if tvshowtime_client.is_authorized():
        wait_for_request(tvshowtime_client, progress, percent)
        tvshowtime_client.mark_episode(tvdb_episode_id,watched_state)


def set_watched_episodes_of_tvshow(tvshowtime_client, kodi_tvshow_id, tvshow_id, progress = None, percent = None):
    if tvshowtime_client.is_token_empty():
        tvshowtime_client.token = __addon__.getSetting('access_token')

    if tvshowtime_client.is_authorized():
        wait_for_request(tvshowtime_client, progress, percent)
        tvshow_info = tvshowtime_client.get_show_detail(tvshow_id)
        if tvshow_info == None:
            log("TVShow " + str(tvshow_id) + "not found")
            return False

        kodi_tvshow_watched_info = get_tvshow_episodes_watched_status(kodi_tvshow_id)
        log(kodi_tvshow_watched_info)
        all_eps_count = tvshow_info['show']['aired_episodes']
        eps_count = 0
        watched_range_from_first_ep = False
        for episode in tvshow_info['show']['episodes']:
            eps_count += 1
            if progress is not None: 
                percent = int(eps_count * 100 / all_eps_count)
                progress.update(percent,__scriptname__,"%s S%02dE%02d" % (tvshow_info['show']['name'], int(episode['season_number']), int(episode['number'])))
            watched_status = check_watched_status_in_kodi(kodi_tvshow_watched_info,episode['season_number'],episode['number'])
            server_watched_status = episode['seen']
            if watched_status == True and int(episode['season_number']) == 1 and int(episode['number']) == 1:
                watched_range_from_first_ep = True
                watched_range_from_first_ep_season = int(episode['season_number'])
                watched_range_from_first_ep_number = int(episode['number'])
            elif watched_status == True and watched_range_from_first_ep == True:
                watched_range_from_first_ep_season = int(episode['season_number'])
                watched_range_from_first_ep_number = int(episode['number'])
            elif watched_status == False and watched_range_from_first_ep == True:
                log(['Range sync up to',watched_range_from_first_ep_season,watched_range_from_first_ep_number,tvshow_info['show']['name']])
                wait_for_request(tvshowtime_client, progress, percent)
                tvshowtime_client.mark_episode_in_range_from_start(tvshow_id,watched_range_from_first_ep_season,watched_range_from_first_ep_number,True)
                watched_range_from_first_ep = False
                log(['Unwatched', int(episode['season_number']), int(episode['number']),tvshow_info['show']['name']])
                if not server_watched_status == watched_status: send_episode_watched_status(tvshowtime_client, episode['id'], watched_status, progress, percent)
            elif watched_status == True and watched_range_from_first_ep == False:
                log(['Mark episode', int(episode['season_number']), int(episode['number']),tvshow_info['show']['name']])
                if not server_watched_status == watched_status: send_episode_watched_status(tvshowtime_client, episode['id'], watched_status, progress, percent)
            else:
                log(['Unwatched', int(episode['season_number']), int(episode['number']),tvshow_info['show']['name']])
                if not server_watched_status == watched_status: send_episode_watched_status(tvshowtime_client, episode['id'], watched_status, progress, percent)

        if watched_range_from_first_ep == True:
            log(['Range sync up to',watched_range_from_first_ep_season,watched_range_from_first_ep_number,tvshow_info['show']['name']])
            wait_for_request(tvshowtime_client, progress, percent)
            tvshowtime_client.mark_episode_in_range_from_start(tvshow_id,watched_range_from_first_ep_season,watched_range_from_first_ep_number,True)


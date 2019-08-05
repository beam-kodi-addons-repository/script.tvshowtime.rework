#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re,sys
import urllib,urllib2
import time

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

from utilities import log

# def log(message, input_json = False):
#     if input_json == True:
#         print("###: " + json.dumps(message,sort_keys=True,indent=4, separators=(',', ': ')))
#     else:
#         print("###: " + str(message))

class TVShowTimeClient(object):

    def __init__(self, auth_token = None):
        self.base_api_url = 'https://api.tvtime.com/v1/'
        self.client_id = 'pr4GUjdRKnLLxeLzCdZL'
        self.client_secret = 'bhaP1sNmuvaUoH45fCi1DaEwKNrheqcvqrUm81sE'
        self.device_code = None
        self.token = auth_token
        self.rate_limit_remaining = None
        self.rate_limit_reset = None

        self.authorized = None

        self.clear_cache()

    def clear_cache(self):
        log('Clearing cache')
        self.cache = { 'last_mark_watch' : None }

    def is_token_empty(self):
        if self.token == '' or self.token is None:
            return True
        else:
            return False

    def store_api_rate(self, headers):
        if headers.get("X-RateLimit-Remaining"):
            self.rate_limit_remaining = int(headers.get("X-RateLimit-Remaining"))
            self.rate_limit_reset = int(headers.get("X-RateLimit-Reset"))
        log({'rate_remain' : self.rate_limit_remaining, 'rate_reset_at' : self.rate_limit_reset})

    def available_request(self):
        if self.rate_limit_reset is None: return True
        if self.rate_limit_remaining > 1: return True
        if self.rate_limit_reset - time.time() < -5: return True
        return False

    def wait_for_available_request(self):
        while True:
            if self.available_request():
                break
            else:
                yield int(self.rate_limit_reset - time.time()) + 5
                time.sleep(10)

    def get_code(self):
        res = urllib2.urlopen(self.base_api_url + "oauth/device/code", 
            urllib.urlencode({"client_id" : self.client_id})
        )
        data = json.loads(res.read()) # device_code, verification_url, interval, expires_in, user_code, result
        log(data)
        return data

    def wait_for_authorize(self,get_code_data):
        if get_code_data['result'] == 'KO': yield {'result' : 'KO', 'error' : get_code_date['message']}
        for wait_index in range(int(get_code_data['expires_in'] / (get_code_data['interval'] + 1))):
            res = urllib2.urlopen(self.base_api_url + "oauth/access_token", 
                urllib.urlencode({
                    "client_id" : self.client_id,
                    "client_secret" : self.client_secret,
                    "code" : get_code_data['device_code']
                })
            )
            data = json.loads(res.read())
            log(data)
            if data['result'] == 'OK': break
            if data['message'] == 'Invalid code': break
            yield data
            time.sleep(int(get_code_data['interval']) + 1)
        yield data

    def get_authorization(self,authorize):
        if authorize['result'] == 'KO': return ''
        return authorize['access_token']

    def is_authorized(self):
        if self.is_token_empty(): return False
        if self.authorized == None: self.authorized = self.check_authorization() != False
        log("Is authorized ~ " + str(self.authorized))
        return self.authorized

    def check_authorization(self):
        if self.is_token_empty(): return False
        try:
            res = urllib2.urlopen(self.base_api_url + "user?access_token=" + self.token)
            data = json.loads(res.read())
        except urllib2.HTTPError as res:
            data = { 'result' : 'KO', 'error' : res }
        self.store_api_rate(res.headers)
        log(data)
        return data['user']['name'] if data['result'] == "OK" else False 

    def get_show_detail(self, tvdb_show_id):
        try:
            res = urllib2.urlopen(self.base_api_url + "/show" + "?show_id=" + str(tvdb_show_id) +"&include_episodes=1&access_token=" + self.token)
            data = json.loads(res.read())
        except urllib2.HTTPError as res:
            data = { 'result' : 'KO', 'error' : res }
        self.store_api_rate(res.headers)
        # log(data)
        if data['result'] == "OK":
            # if data['show']['episodes']:
            #     data['show']['seasons'] = {}
            #     for episode in data['show']['episodes']:
            #         if episode['season_number'] in data['show']['seasons'].keys():
            #             if int(episode['number']) > data['show']['seasons'][episode['season_number']]: data['show']['seasons'][episode['season_number']] = int(episode['number'])
            #         else:
            #             data['show']['seasons'][episode['season_number']] = int(episode['number'])
            return data
        else:
            return None

    def follow_show(self, tvdb_show_id, follow_status = True):
        action = "follow" if follow_status == True else "unfollow"
        log("Follow show: " + action + " - " + str(tvdb_show_id))
        try:
            res = urllib2.urlopen(self.base_api_url +  action + "?access_token=" + self.token,
                urllib.urlencode({ "show_id" : tvdb_show_id })
            )
            data = json.loads(res.read())
        except urllib2.HTTPError as res:
            data = { 'result' : 'KO', 'error' : res }
        self.store_api_rate(res.headers)
        log(data)
        return data["result"] == "OK"


    def mark_episode(self,tvdb_episode_id,watched = True):
        action = "checkin" if watched == True else "checkout"
        log("Mark episode: " + action + " - " + str(tvdb_episode_id))

        if self.cache['last_mark_watch'] and self.cache['last_mark_watch']['episode_id'] == tvdb_episode_id and self.cache['last_mark_watch']['status'] == watched:
            log('Found in last cache, skipping sending on server')
            return True

        try:
            res = urllib2.urlopen(self.base_api_url +  action + "?access_token=" + self.token,
                urllib.urlencode({
                    "episode_id" : tvdb_episode_id,
                    "publish_on_ticker" : 0,
                    "publish_on_twitter": 0
                })
            )
            data = json.loads(res.read())
        except urllib2.HTTPError as res:
            data = { 'result' : 'KO', 'error' : res }
        self.store_api_rate(res.headers)
        log(data)
        if data["result"] == "OK": self.cache['last_mark_watch'] = {'episode_id' : tvdb_episode_id , 'status' : watched }
        return data["result"] == "OK"

    def mark_episode_in_range_from_start(self,tvdb_show_id, last_season = None, last_episode = None, watched = True):
        action = "show_progress" if watched == True else "delete_show_progress"
        log("Mark episodes in range: " + action + " - " + str(tvdb_show_id) + " / " + str(last_season) + " / " + str(last_episode))
        try:
            values = { "show_id" : int(tvdb_show_id) }
            if last_season: values['season'] = int(last_season)
            if last_episode: values['episode'] = int(last_episode)
            res = urllib2.urlopen(self.base_api_url +  action + "?access_token=" + self.token,
                urllib.urlencode(values)
            )
            data = json.loads(res.read())
        except urllib2.HTTPError as res:
            data = { 'result' : 'KO', 'error' : res }
        self.store_api_rate(res.headers)
        log(data)
        return data["result"] == "OK"

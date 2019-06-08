import requests
import json
import time
from base64 import b64encode
from urllib.parse import urlencode, urlparse, parse_qsl


class Google:
    def __init__(self, config):
        with open('config/google_auth.json') as json_file:
            self.auth = json.load(json_file)

        self.api_key = config.get('api_key')
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.redirect_uri = config.get('redirect_uri')
        self.scope = "https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtubepartner https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/youtube.force-ssl"

        self.access_token = self.auth.get('access_token')
        self.refresh_token = self.auth.get('refresh_token')

        try:
            self.expiration = int(self.auth.get('expiration'))
        except TypeError:
            self.expiration = 0

        if not (self.access_token and self.refresh_token and self.expiration):
            print("Please login to google:")
            print(self.gen_auth_url())
            url = input("[?] Which URL have you been redirected to?: ")
            code = self._parse_auth_redirect(url)
            self._request_tokens(code)

    def gen_auth_url(self):
        return "https://accounts.google.com/o/oauth2/auth?{}".format(
            urlencode({
                "client_id": self.client_id,
                "response_type": "code",
                "redirect_uri": self.redirect_uri,
                "scope": self.scope,
                "access_type": "offline",
                "include_granted_scopes": 'true'
            })
        )

    def _parse_auth_redirect(self, url):
        query = dict(parse_qsl(urlparse(url).query))
        return query['code']

    def _post(self, url="", data={}, json={}, headers={}, **kwargs):
        if 0 < self.expiration < time.time() + 5 and "refresh_token" not in kwargs:
            self._refresh_tokens()

        try:
            rq = requests.post(url=url, data=data, json=json, headers=headers)
            rq.raise_for_status()
            return rq.json()
        except requests.exceptions.HTTPError as err:
            raise Exception(err, rq.text) from None

    def _get(self, url="", params={}, headers={}):
        if 0 < self.expiration < time.time() + 5:
            self._refresh_tokens()

        try:
            rq = requests.get(url=url, params=params, headers=headers)
            rq.raise_for_status()
            return rq.json()
        except requests.exceptions.HTTPError as err:
            raise Exception(err, rq.text) from None

    def _request_tokens(self, code):
        res = self._post(url="https://www.googleapis.com/oauth2/v4/token", data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        })

        self.auth['access_token'] = res.get('access_token')
        self.auth['refresh_token'] = res.get('refresh_token')
        self.auth['expiration'] = int(res.get('expires_in')) + time.time()

        return self._save_tokens()

    def _refresh_tokens(self):
        res = self._post(url="https://www.googleapis.com/oauth2/v4/token", data={
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }, refresh_token=True)

        self.auth['access_token'] = res.get('access_token')
        self.auth['expiration'] = int(res.get('expires_in')) + time.time()

        return self._save_tokens()

    def _save_tokens(self):
        self.access_token = self.auth['access_token']
        self.refresh_token = self.auth['refresh_token']

        with open("config/google_auth.json", "w") as json_file:
            return json.dump(self.auth, json_file)

    def search(self, search_term=""):
        res = self._get("https://www.googleapis.com/youtube/v3/search", params={
            "key": self.api_key,
            "part": "snippet",
            "type": "video",
            "q": search_term,
            "maxResults": 1
        })

        return res.get("items")[0].get("id").get("videoId")

    def create_playlist(self, title=""):
        return self._post("https://www.googleapis.com/youtube/v3/playlists?{}".format(
            urlencode({
                "key": self.api_key,
                "part": "snippet"
            })
        ), json={
            "snippet": {
                "title": title
            }
        }, headers={
            "Authorization": "Bearer {}".format(self.access_token)
        })

    def add_video(self, playlist_id, video_id):
        return self._post("https://www.googleapis.com/youtube/v3/playlistItems?{}".format(
            urlencode({
                "key": self.api_key,
                "part": "snippet"
            })), json={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
        }, headers={
            "Authorization": "Bearer {}".format(self.access_token)
        })

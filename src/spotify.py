import requests
import json
import time
from base64 import b64encode
from urllib.parse import urlencode, urlparse, parse_qsl


class Spotify:
    def __init__(self, config):
        with open('config/spotify_auth.json') as json_file:
            self.auth = json.load(json_file)

        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.redirect_uri = config.get('redirect_uri')
        self.scope = "playlist-read-private playlist-read-collaborative user-read-email user-read-private user-read-birthdate"

        self.access_token = self.auth.get('access_token')
        self.refresh_token = self.auth.get('refresh_token')

        try:
            self.expiration = int(self.auth.get('expiration'))
        except TypeError:
            self.expiration = 0

        if not (self.access_token and self.refresh_token and self.expiration):
            print("Please login to spotify:")
            print(self.gen_auth_url())
            url = input("[?] Which URL have you been redirected to?: ")
            code = self._parse_auth_redirect(url)
            self._request_tokens(code)

    def gen_auth_url(self):
        return "https://accounts.spotify.com/authorize?{}".format(
            urlencode({
                "client_id": self.client_id,
                "response_type": "code",
                "redirect_uri": self.redirect_uri,
                "scope": self.scope,
                "show_dialog": "false"
            })
        )

    def _parse_auth_redirect(self, url):
        query = dict(parse_qsl(urlparse(url).query))
        return query['code']

    def _post(self, url="", data={}, headers={}, **kwargs):
        if 0 < self.expiration < time.time() + 5 and "refresh_token" not in kwargs:
            self._refresh_tokens()

        try:
            rq = requests.post(url=url, data=data, headers=headers)
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

    def _next(self, items, url):
        while url:
            response = self._get(url, headers={
                "Authorization": "Bearer {}".format(self.access_token)
            })

            for i in response.get("items"):
                items.append(i)

            url = response.get('next')

        return items

    def _request_tokens(self, code):
        res = self._post(url="https://accounts.spotify.com/api/token", data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }, headers={
            "Authorization": "Basic {}".format(
                str(b64encode("{}:{}".format(self.client_id,
                                             self.client_secret).encode()), "utf-8")
            )
        })

        self.auth['access_token'] = res.get('access_token')
        self.auth['refresh_token'] = res.get('refresh_token')
        self.auth['expiration'] = int(res.get('expires_in')) + time.time()
        return self._save_tokens()

    def _refresh_tokens(self):
        res = self._post(url="https://accounts.spotify.com/api/token", data={
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }, headers={
            "Authorization": "Basic {}".format(
                str(b64encode("{}:{}".format(self.client_id,
                                             self.client_secret).encode()), "utf-8")
            )
        }, refresh_token=True)

        self.auth['access_token'] = res.get('access_token')
        self.auth['expiration'] = int(res.get('expires_in')) + time.time()
        return self._save_tokens()

    def _save_tokens(self):
        self.access_token = self.auth['access_token']
        self.refresh_token = self.auth['refresh_token']

        with open("config/spotify_auth.json", "w") as json_file:
            return json.dump(self.auth, json_file)

    def user_playlists(self):
        res = self._get("https://api.spotify.com/v1/me/playlists", headers={
            "Authorization": "Bearer {}".format(self.access_token)
        })

        items = res.get('items')
        if res.get('next'):
            items = self._next(items, res.get('next'))

        return items

    def playlist_tracks(self, playlist_id):
        res = self._get("https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id), headers={
            "Authorization": "Bearer {}".format(self.access_token)
        })

        items = res.get('items')
        if res.get('next'):
            items = self._next(items, res.get('next'))

        return items

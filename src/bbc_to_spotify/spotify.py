import datetime as dt
import logging
import time
from typing import Literal, Optional
from urllib.parse import urljoin

import requests
from pydantic import BaseModel

import bbc_to_spotify.utils as utils


class NoRefreshTokenError(Exception):
    pass


class SearchParams(BaseModel):
    q: str
    type: str
    market: str | None = None
    limit: int


class AddItemsToPlaylistParams(BaseModel):
    uris: str


class GetAccessTokenBody(BaseModel):
    client_id: str
    client_secret: str
    grant_type: Literal["refresh_token", "client_credentials"]
    refresh_token: str | None = None


class TrackURI(BaseModel):
    uri: str


class RemovePlaylistItemsBody(BaseModel):
    tracks: list[TrackURI]


class ChangePlaylistDetailsBody(BaseModel):
    name: str | None = None
    public: bool | None = None
    collaborative: bool | None = None
    description: str | None = None


class ArtistModel(BaseModel):
    name: str
    uri: str
    id: str


class AlbumModel(BaseModel):
    name: str
    artists: list[ArtistModel]
    uri: str
    id: str


class TrackModel(BaseModel):
    album: AlbumModel
    artists: list[ArtistModel]
    name: str
    uri: str
    id: str
    popularity: int


class TrackWithMetaModel(BaseModel):
    added_at: dt.datetime
    track: TrackModel


class TracksWithMetaModel(BaseModel):
    items: list[TrackWithMetaModel]


class TracksModel(BaseModel):
    items: list[TrackModel]


class PlaylistMetaModel(BaseModel):
    collaborative: bool
    description: str
    name: str
    public: bool
    uri: str
    id: str


class PlaylistModel(PlaylistMetaModel):
    tracks: TracksWithMetaModel
    collaborative: bool
    description: str
    name: str
    public: bool
    uri: str
    id: str


class GetPlaylistsResponse(BaseModel):
    items: list[PlaylistMetaModel]


class GetPlaylistResponse(PlaylistModel):
    tracks: TracksWithMetaModel


class TrackSearchResponse(BaseModel):
    tracks: TracksModel


def check_access_token(func):
    def wrapper(*args, **kwargs):
        spotify: Spotify = args[0]
        if spotify.token_ts is None:
            logging.debug("No access token. Getting a new one one.")
            spotify.get_new_access_token()
        elif time.time() > spotify.token_ts + spotify.access_token_timeout - 300:
            logging.debug("Access token out of date. getting a new one.")
            spotify.get_new_access_token()

        res = func(*args, **kwargs)

        return res

    return wrapper


class Spotify:
    base_url = "https://api.spotify.com"
    accounts_base_url = "https://accounts.spotify.com"
    version = "v1"
    access_token_timeout = 3600

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        grant_type: Literal["refresh_token", "client_credentials"],
        refresh_token: str | None = None,
    ):
        if grant_type == "refresh_token" and refresh_token is None:
            logging.error("No refresh token provided")
            raise NoRefreshTokenError(
                "To use the grant type 'refresh_token' a valid refresh token must be"
                " provided."
            )

        self.client_id = client_id
        self.client_secret = client_secret
        self.grant_type = grant_type
        self.refresh_token = refresh_token

        self.access_token: str | None = None
        self.token_ts: float | None = None
        self.session = requests.session()

    def api_call(
        self,
        url: str,
        method: Literal["get", "put", "post", "delete"] = "get",
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        json: Optional[dict] = None,
        timeout_s: int = 30,
    ) -> requests.Response:

        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            json=json,
            timeout=timeout_s,
        )
        response.raise_for_status()
        return response

    @property
    def authorization_headers(self) -> dict:
        headers = {"Authorization": "Bearer {}".format(self.access_token)}
        return headers

    def get_new_access_token(self):
        url_ext = "/api/token"
        url = urljoin(base=self.accounts_base_url, url=url_ext)
        body = GetAccessTokenBody(
            client_id=self.client_id,
            client_secret=self.client_secret,
            grant_type=self.grant_type,
            refresh_token=self.refresh_token,
        ).model_dump()

        response = self.api_call(
            url=url,
            method="post",
            data=body,
        )
        content = response.json()
        self.access_token = content["access_token"]
        self.token_ts = time.time()

    @check_access_token
    def search(
        self,
        query: str,
        thing_type: str,
        market: Optional[str] = None,
        limit: int = 20,
    ):
        url_ext = f"{self.version}/search"
        url = urljoin(base=self.base_url, url=url_ext)

        params = SearchParams(
            q=query, type=thing_type, market=market, limit=limit
        ).model_dump(exclude_none=True)

        response = self.api_call(
            url=url,
            method="get",
            headers=self.authorization_headers,
            params=params,
        )

        return response.json()

    @check_access_token
    def get_track(self, track_id: str, market: Optional[str] = None) -> TrackModel:
        url_ext = f"{self.version}/tracks/{track_id}"
        if market is not None:
            url_ext += f"?market={market}"
        url = urljoin(base=self.base_url, url=url_ext)

        response = self.api_call(
            url=url, method="get", headers=self.authorization_headers
        )

        track = TrackModel.model_validate(response.json())

        return track

    @check_access_token
    def get_user_playlists(self, user_id: str) -> list[PlaylistMetaModel]:
        url_ext = f"{self.version}/users/{user_id}/playlists"
        url = urljoin(base=self.base_url, url=url_ext)

        response = self.api_call(
            url=url, method="get", headers=self.authorization_headers
        )

        playlists = GetPlaylistsResponse.model_validate(response.json()).items

        return playlists

    @check_access_token
    def get_playlist(self, playlist_id: str) -> PlaylistModel:
        url_ext = f"{self.version}/playlists/{playlist_id}"
        url = urljoin(base=self.base_url, url=url_ext)
        response = self.api_call(
            url=url, method="get", headers=self.authorization_headers
        )
        response_json = response.json()
        playlist = PlaylistModel.model_validate(response_json)
        next = response_json["tracks"].get("next")
        i = 0
        while next is not None:
            i += 1
            logging.debug(f"Paginating...{i}")
            response = self.api_call(
                url=next, method="get", headers=self.authorization_headers
            )
            response_json = response.json()
            next = response_json.get("next")
            tracks = TracksWithMetaModel.model_validate(response_json)
            playlist.tracks.items.extend(tracks.items)

        logging.debug(f"{len(playlist.tracks.items)} tracks retrieved.")

        return playlist

    @check_access_token
    def add_to_playlist(self, playlist_id: str, track_uris: list[str]):
        url_ext = f"{self.version}/playlists/{playlist_id}/tracks"
        url = urljoin(base=self.base_url, url=url_ext)

        for _track_uris in utils.batch_list(track_uris, batch_size=100):
            params = AddItemsToPlaylistParams(uris=",".join(_track_uris)).model_dump()

            logging.debug(f"Adding: {params}.")

            self.api_call(
                url, method="post", headers=self.authorization_headers, params=params
            )

    @check_access_token
    def remove_from_playlist(self, playlist_id: str, track_uris: list[str]):
        url_ext = f"{self.version}/playlists/{playlist_id}/tracks"
        url = urljoin(base=self.base_url, url=url_ext)

        headers = self.authorization_headers
        headers.update({"Content-Type": "application/json"})

        tracks = [TrackURI(uri=uri) for uri in track_uris]

        for _tracks in utils.batch_list(tracks, batch_size=100):
            data = RemovePlaylistItemsBody(tracks=_tracks).model_dump()
            logging.debug(f"Removing: {data}.")
            self.api_call(
                url=url,
                method="delete",
                headers=headers,
                json=data,
            )

    @check_access_token
    def change_playlist_details(
        self,
        playlist_id: str,
        name: Optional[str] = None,
        public: Optional[bool] = None,
        collaborative: Optional[bool] = None,
        description: Optional[str] = None,
    ):
        url_ext = f"{self.version}/playlists/{playlist_id}"
        url = urljoin(base=self.base_url, url=url_ext)

        headers = self.authorization_headers
        headers.update({"Content-Type": "application/json"})

        data = ChangePlaylistDetailsBody(
            name=name,
            public=public,
            collaborative=collaborative,
            description=description,
        ).model_dump(exclude_none=True)

        self.api_call(url, method="put", headers=self.authorization_headers, json=data)

    @check_access_token
    def search_for_track_by_artist_and_track_name(
        self, artist: str, track_name: str, market: Optional[str] = None
    ) -> list[TrackModel]:
        query = f"artist:{artist} track:{track_name}"
        logging.debug(f"Searching for track. Query: {query}")
        result = self.search(
            query=query,
            thing_type="track",
            market=market,
        )

        track_search_response = TrackSearchResponse.model_validate(result)

        tracks = track_search_response.tracks.items

        return tracks

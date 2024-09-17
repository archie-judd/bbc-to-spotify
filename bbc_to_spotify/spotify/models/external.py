import datetime as dt
from typing import Literal, Self

from pydantic import BaseModel, model_validator


class UserModel(BaseModel):
    display_name: str
    id: str
    uri: str


class SearchParams(BaseModel):
    q: str
    type: str
    market: str | None = None
    limit: int


class AddItemsToPlaylistBody(BaseModel):
    uris: str
    position: int | None = None


class GetAccessTokenBody(BaseModel):
    client_id: str
    client_secret: str
    grant_type: Literal["refresh_token", "client_credentials"]
    refresh_token: str | None = None


class TrackURI(BaseModel):
    uri: str


class CreatePlaylistBody(BaseModel):
    name: str
    public: bool | None = None
    description: str | None = None
    collaborative: bool | None = None

    @model_validator(mode="after")
    def check_not_public_and_collaborative(self) -> Self:
        if self.public and self.collaborative:
            raise ValueError("Public and collaborative cannot both be True.")
        return self


class UpdatePlaylistBody(BaseModel):
    snapshot_id: str
    uris: list[str] | None = None
    range_start: int | None = None
    insert_before: int | None = None
    range_length: int | None = None

    @model_validator(mode="after")
    def check_uris_or_range(self) -> Self:
        if self.uris and (self.range_start or self.insert_before or self.range_length):
            raise ValueError(
                "Must provide either uris, or range parameters (range_start, insert_before and optionally range_length)"
            )
        elif self.range_start and not self.insert_before:
            raise ValueError(
                "Must provide either uris, or range parameters (range_start, insert_before and optionally range_length)"
            )
        return self


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
    name: str
    public: bool
    uri: str
    id: str
    description: str | None = None


class PlaylistModel(PlaylistMetaModel):
    tracks: TracksWithMetaModel
    collaborative: bool
    name: str
    public: bool
    uri: str
    id: str
    snapshot_id: str
    description: str | None = None


class UpdatePlaylistResponse(BaseModel):
    snapshot_id: str


class GetPlaylistsResponse(BaseModel):
    items: list[PlaylistMetaModel]


class GetPlaylistResponse(PlaylistModel):
    tracks: TracksWithMetaModel


class TrackSearchResponse(BaseModel):
    tracks: TracksModel

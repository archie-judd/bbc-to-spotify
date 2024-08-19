from dataclasses import dataclass
from typing import Self

from bbc_to_spotify.models.spotify import (
    AlbumModel,
    ArtistModel,
    PlaylistModel,
    TrackModel,
    UserModel,
)


@dataclass
class ScrapedTrack:
    name: str
    artist: str


@dataclass(frozen=True)
class User:
    display_name: str
    id: str
    uri: str

    @classmethod
    def from_external(cls, user_model: UserModel) -> Self:
        user = cls(
            display_name=user_model.display_name, id=user_model.id, uri=user_model.uri
        )
        return user


@dataclass(frozen=True)
class Artist:
    name: str
    uri: str
    id: str

    @classmethod
    def from_external(cls, artist_model: ArtistModel) -> Self:
        artist = cls(name=artist_model.name, uri=artist_model.uri, id=artist_model.id)
        return artist


@dataclass(frozen=True)
class Album:
    name: str
    artists: list[Artist]
    uri: str
    id: str

    @classmethod
    def from_external(cls, album_model: AlbumModel) -> Self:
        artists = [
            Artist.from_external(artist_model) for artist_model in album_model.artists
        ]
        album = cls(
            name=album_model.name,
            artists=artists,
            uri=album_model.uri,
            id=album_model.id,
        )
        return album


@dataclass(frozen=True)
class Track:
    album: Album
    artists: list[Artist]
    name: str
    uri: str
    id: str
    popularity: int

    @classmethod
    def from_external(cls, track_model: TrackModel) -> Self:
        album = Album.from_external(track_model.album)
        artists = [
            Artist.from_external(artist_model) for artist_model in track_model.artists
        ]
        track = cls(
            album=album,
            artists=artists,
            name=track_model.name,
            uri=track_model.uri,
            id=track_model.id,
            popularity=track_model.popularity,
        )
        return track

    # Could use the track ID, but this can cause duplicates when assessing which
    # tracks are already in the playlist, because the same track may appear in multiple
    # albums, each with a different ID.
    def __hash__(self) -> int:
        artist_names = tuple(sorted(artist.name for artist in self.artists))
        return hash((self.name, artist_names))

    def __eq__(self, other) -> bool:
        return self.__hash__() == other.__hash__()


@dataclass
class Playlist:
    tracks: list[Track]
    collaborative: bool
    name: str
    public: bool
    uri: str
    id: str
    description: str | None = None

    @classmethod
    def from_external(cls, playlist_model: PlaylistModel) -> Self:

        tracks = [
            Track.from_external(track_with_meta_model.track)
            for track_with_meta_model in playlist_model.tracks.items
        ]

        playlist = cls(
            tracks=tracks,
            collaborative=playlist_model.collaborative,
            description=playlist_model.description,
            name=playlist_model.name,
            public=playlist_model.public,
            uri=playlist_model.uri,
            id=playlist_model.id,
        )

        return playlist

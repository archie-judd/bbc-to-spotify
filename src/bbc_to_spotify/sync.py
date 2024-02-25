import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Self
from zoneinfo import ZoneInfo

from bbc_to_spotify.authorize import Credentials
from bbc_to_spotify.scrape import scrape_tracks_from_playlist_page
from bbc_to_spotify.spotify import (
    AlbumModel,
    ArtistModel,
    PlaylistModel,
    Spotify,
    TrackModel,
)
from bbc_to_spotify.station import Station, get_playlist_url

SPECIAL_CHARACTERS_PATTEN = r"[^ \w+-.]"
# match trailing, leading, or spaces succeeded by another space
STRIP_WHITESPACE_PATTERN = r"^\s+|\s$|\s+(?=\s)"


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
    description: str
    name: str
    public: bool
    uri: str
    id: str

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


def make_updated_playlist_description(description: str) -> str:
    ts = datetime.now(tz=ZoneInfo("Europe/London")).strftime("%d-%m-%Y %H:%M:%S (%Z)")
    description_without_date = "Last updated: ".join(
        description.split("Last updated: ")[0:-1]
    )
    new_description = f"{description_without_date} Last updated: {ts}"
    return new_description


def has_special_characters(string: str) -> bool:
    res = re.search(pattern=SPECIAL_CHARACTERS_PATTEN, string=string)
    has = bool(res)
    return has


def remove_special_characters_and_strip_whitespace(string: str) -> str:
    string = re.sub(pattern=SPECIAL_CHARACTERS_PATTEN, repl="", string=string)
    string = re.sub(pattern=STRIP_WHITESPACE_PATTERN, repl="", string=string)
    return string


def get_playlist(spotify_client: Spotify, playlist_id: str) -> Playlist:
    playlist_model = spotify_client.get_playlist(playlist_id=playlist_id)
    playlist = Playlist.from_external(playlist_model)
    return playlist


def get_tracks_by_artist_and_track_name(
    spotify_client: Spotify,
    artist: str,
    track_name: str,
    retry_without_special_characters: bool = True,
) -> set[Track]:
    track_models = spotify_client.search_for_track_by_artist_and_track_name(
        artist=artist, track_name=track_name
    )

    if not track_models and (
        retry_without_special_characters
        and (has_special_characters(artist) or has_special_characters(track_name))
    ):
        artist_ = remove_special_characters_and_strip_whitespace(artist)
        track_name_ = remove_special_characters_and_strip_whitespace(track_name)
        track_models = spotify_client.search_for_track_by_artist_and_track_name(
            artist=artist_, track_name=track_name_
        )

    tracks = {Track.from_external(track_model) for track_model in track_models}

    return tracks


def scrape_tracks_and_get_from_spotify(
    spotify_client: Spotify, station: Station
) -> list[Track]:

    playlist_url = get_playlist_url(station=station)

    scraped_radio_6_tracks = scrape_tracks_from_playlist_page(playlist_url=playlist_url)

    spotify_radio_6_tracks: list[Track] = []
    for scraped_track in scraped_radio_6_tracks:
        spotify_tracks = get_tracks_by_artist_and_track_name(
            spotify_client=spotify_client,
            artist=scraped_track.artist,
            track_name=scraped_track.name,
        )
        if spotify_tracks:
            tracks = sorted(
                list(spotify_tracks),
                key=lambda x: (x.popularity, x.id),
                reverse=True,  # make deterministic
            )
            spotify_radio_6_tracks.append(tracks[0])
        else:
            logging.warning(f"Could not find track on Spotify: {scraped_track}")

    return spotify_radio_6_tracks


def add_tracks(
    spotify_client: Spotify,
    dest_playlist_id: str,
    dest_tracks: list[Track],
    source_tracks: list[Track],
    remove_duplicates: bool,
    dry_run: bool,
):

    if remove_duplicates:
        duplicates = set(source_tracks).intersection(set(dest_tracks))
        tracks_to_add = list(set(source_tracks).difference(duplicates))
    else:
        tracks_to_add = source_tracks

    if tracks_to_add:
        logging.info(f"Addings these tracks: {[track.name for track in source_tracks]}")
        if not dry_run:
            spotify_client.add_to_playlist(
                playlist_id=dest_playlist_id,
                track_uris=[track.uri for track in tracks_to_add],
            )
        else:
            logging.info("No tracks added (dry run)")
    else:
        logging.info(f"No tracks to add")


def prune_and_add_tracks(
    spotify_client: Spotify,
    dest_playlist_id: str,
    dest_tracks: list[Track],
    source_tracks: list[Track],
    dry_run: bool,
):

    logging.info("Pruning destination playlist")
    # Deduplicate the destination playlist, and remove any tracks that are not in the
    # source playlist.
    tracks_to_stay = set(t for t in source_tracks if dest_tracks.count(t) == 1)
    tracks_to_remove = set(dest_tracks).difference(tracks_to_stay)

    if tracks_to_remove:
        logging.info(
            f"Removing these tracks: {[track.name for track in tracks_to_remove]}"
        )
        if not dry_run:
            spotify_client.remove_from_playlist(
                playlist_id=dest_playlist_id,
                track_uris=[track.uri for track in tracks_to_remove],
            )
        else:
            logging.info("No tracks removed (dry run)")
    else:
        logging.info("No tracks to remove")

    # Only add tracks that are not in the remaining source tracks
    add_tracks(
        spotify_client=spotify_client,
        dest_playlist_id=dest_playlist_id,
        dest_tracks=list(tracks_to_stay),
        source_tracks=source_tracks,
        remove_duplicates=True,
        dry_run=dry_run,
    )


def add_timestamp_to_desc(
    spotify_client: Spotify, playlist: Playlist, dry_run: bool = False
):
    logging.info("Updating playlist description")
    updated_description = make_updated_playlist_description(playlist.description)
    if not dry_run:
        spotify_client.change_playlist_details(
            playlist_id=playlist.id,
            description=updated_description,
        )
    else:
        logging.info("Playlist description not updated (dry run)")


def sync(
    credentials: Credentials,
    playlist_id: str,
    source: Station,
    remove_duplicates: bool,
    prune_dest: bool,
    update_description: bool,
    dry_run: bool,
):

    spotify_client = Spotify(
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        grant_type="refresh_token",
        refresh_token=credentials.refresh_token,
    )

    source_tracks = scrape_tracks_and_get_from_spotify(
        spotify_client=spotify_client, station=source
    )

    dest_playlist = get_playlist(spotify_client=spotify_client, playlist_id=playlist_id)

    if prune_dest:
        prune_and_add_tracks(
            spotify_client=spotify_client,
            dest_playlist_id=dest_playlist.id,
            dest_tracks=dest_playlist.tracks,
            source_tracks=source_tracks,
            dry_run=dry_run,
        )
    else:
        add_tracks(
            spotify_client=spotify_client,
            dest_playlist_id=dest_playlist.id,
            dest_tracks=dest_playlist.tracks,
            source_tracks=source_tracks,
            remove_duplicates=remove_duplicates,
            dry_run=dry_run,
        )

    if update_description:
        add_timestamp_to_desc(
            spotify_client=spotify_client, playlist=dest_playlist, dry_run=dry_run
        )

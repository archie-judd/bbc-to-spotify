import logging
import re
from typing import Any

from bbc_to_spotify.models.internal import Playlist, Track
from bbc_to_spotify.scraping import scrape_tracks_from_playlist_page
from bbc_to_spotify.spotify import Spotify
from bbc_to_spotify.utils import Station, get_playlist_url

SPECIAL_CHARACTERS_PATTEN = r"[^ \w+-.]"
# match trailing, leading, or spaces succeeded by another space
STRIP_WHITESPACE_PATTERN = r"^\s+|\s$|\s+(?=\s)"


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


def add_tracks_to_playlist(
    spotify_client: Spotify,
    playlist_id: str,
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
                playlist_id=playlist_id,
                track_uris=[track.uri for track in tracks_to_add],
            )
        else:
            logging.info("No tracks added (dry run).")
    else:
        logging.info(f"No tracks to add.")

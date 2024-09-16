import logging
import re

from bbc_to_spotify.scraping.scraping import scrape_tracks_from_playlist_page
from bbc_to_spotify.spotify.models.internal import Playlist, Track
from bbc_to_spotify.spotify.spotify import Spotify
from bbc_to_spotify.utils import Station, get_playlist_url

logger = logging.getLogger(__name__)

SPECIAL_CHARACTERS_PATTEN = r"[^ \w+-.]"
WHITESPACE_PATTERN = r"^\s+|\s$|\s+(?=\s)"
FEATURED_PATTERN = r"feat.*|ft.*|featuring.*"


def is_simple_track_or_artist(string: str) -> bool:
    special_chars_match = re.search(pattern=SPECIAL_CHARACTERS_PATTEN, string=string)
    whitespace_match = re.search(pattern=WHITESPACE_PATTERN, string=string)
    featured_match = re.search(pattern=FEATURED_PATTERN, string=string)
    is_simple_string = (
        special_chars_match is None
        and whitespace_match is None
        and featured_match is None
    )
    return is_simple_string


def simplify_track_or_artist(string: str) -> str:
    string = re.sub(pattern=SPECIAL_CHARACTERS_PATTEN, repl="", string=string)
    string = re.sub(pattern=FEATURED_PATTERN, repl="", string=string)
    string = re.sub(pattern=WHITESPACE_PATTERN, repl="", string=string)
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
        and (
            not is_simple_track_or_artist(artist)
            or not is_simple_track_or_artist(track_name)
        )
    ):
        logger.debug(
            "Could not find track. Retrying with simplified artist and track names."
        )
        artist_ = simplify_track_or_artist(artist)
        track_name_ = simplify_track_or_artist(track_name)
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
            logger.info(f"Successfully found track on Spotify: {scraped_track}")
            spotify_radio_6_tracks.append(tracks[0])
        else:
            logger.warning(f"Could not find track on Spotify: {scraped_track}")

    return spotify_radio_6_tracks


def add_tracks_to_playlist(
    spotify_client: Spotify,
    playlist_id: str,
    dest_tracks: list[Track],
    source_tracks: list[Track],
    remove_duplicates: bool,
    prepend: bool,
    dry_run: bool,
):

    if remove_duplicates:
        duplicates = set(source_tracks).intersection(set(dest_tracks))
        tracks_to_add = set(source_tracks).difference(duplicates)
    else:
        tracks_to_add = set(source_tracks)

    if tracks_to_add:
        logger.info(f"Addings these tracks: {[track.name for track in tracks_to_add]}")
        if not dry_run:
            spotify_client.add_to_playlist(
                playlist_id=playlist_id,
                track_uris=[track.uri for track in tracks_to_add],
                position=None if not prepend else 0,
            )
        else:
            logger.info("No tracks added (dry run).")
    else:
        logger.info(f"No tracks to add.")

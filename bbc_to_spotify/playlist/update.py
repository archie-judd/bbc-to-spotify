import datetime as dt
import logging
import re
from zoneinfo import ZoneInfo

from bbc_to_spotify.authorize.models.internal import Credentials
from bbc_to_spotify.playlist.utils import (
    Station,
    add_tracks_to_playlist,
    get_playlist,
    scrape_tracks_and_get_from_spotify,
)
from bbc_to_spotify.spotify.models.internal import Playlist, Track
from bbc_to_spotify.spotify.spotify import Spotify

logger = logging.getLogger(__name__)


def make_updated_playlist_description(description: str) -> str:

    PATTERN = r"(?<=Last updated: )\b\d{2}\-\d{2}\-\d{4}\s\d{2}:\d{2}:\d{2}\s\(\w+\)"
    ts = dt.datetime.now(tz=ZoneInfo("Europe/London")).strftime(
        "%d-%m-%Y %H:%M:%S (%Z)"
    )
    logger.debug(
        f"Searching for 'Last updated' timestamp in description: {description}"
    )
    match = re.search(pattern=PATTERN, string=description)
    if match is not None:
        logger.debug(
            f"Found 'Last updated' timestamp: {match}. Performing regex subsitution."
        )
        new_description = re.sub(pattern=PATTERN, repl=ts, string=description, count=1)
    else:
        logger.debug("No 'Last updated' timestamp found. Appending to description.")
        new_description = description + f" Last updated: {ts}"

    return new_description


def add_timestamp_to_desc(
    spotify_client: Spotify, playlist: Playlist, dry_run: bool = False
):
    logger.info("Updating playlist description.")
    if playlist.description:
        description = make_updated_playlist_description(playlist.description)
    else:
        ts = dt.datetime.now(tz=ZoneInfo("Europe/London")).strftime(
            "%d-%m-%Y %H:%M:%S (%Z)"
        )
        description = f"Last updated: {ts}"
    if not dry_run:
        spotify_client.change_playlist_details(
            playlist_id=playlist.id,
            description=description,
        )
    else:
        logger.info("Playlist description not updated (dry run).")


def add_tracks_and_prune_playlist(
    spotify_client: Spotify,
    playlist_id: str,
    dest_tracks: list[Track],
    source_tracks: list[Track],
    prepend: bool,
    dry_run: bool,
):

    logger.info("Pruning destination playlist.")
    # Deduplicate the destination playlist, and remove any tracks that are not in the
    # source playlist.
    tracks_to_stay = set(t for t in source_tracks if dest_tracks.count(t) == 1)
    tracks_to_remove = set(dest_tracks).difference(tracks_to_stay)

    if tracks_to_remove:
        logger.info(
            f"Removing these tracks: {[track.name for track in tracks_to_remove]}"
        )
        if not dry_run:
            spotify_client.remove_from_playlist(
                playlist_id=playlist_id,
                track_uris=[track.uri for track in tracks_to_remove],
            )
        else:
            logger.info("No tracks removed (dry run).")
    else:
        logger.info("No tracks to remove.")

    # Only add tracks that are not in the remaining source tracks
    add_tracks_to_playlist(
        spotify_client=spotify_client,
        playlist_id=playlist_id,
        dest_tracks=list(tracks_to_stay),
        source_tracks=source_tracks,
        remove_duplicates=True,
        prepend=prepend,
        dry_run=dry_run,
    )


def update_playlist(
    credentials: Credentials,
    playlist_id: str,
    source: Station,
    remove_duplicates: bool,
    prune_dest: bool,
    prepend: bool,
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
        add_tracks_and_prune_playlist(
            spotify_client=spotify_client,
            playlist_id=dest_playlist.id,
            dest_tracks=dest_playlist.tracks,
            source_tracks=source_tracks,
            prepend=prepend,
            dry_run=dry_run,
        )
    else:
        add_tracks_to_playlist(
            spotify_client=spotify_client,
            playlist_id=dest_playlist.id,
            dest_tracks=dest_playlist.tracks,
            source_tracks=source_tracks,
            remove_duplicates=remove_duplicates,
            prepend=prepend,
            dry_run=dry_run,
        )

    if update_description:
        add_timestamp_to_desc(
            spotify_client=spotify_client, playlist=dest_playlist, dry_run=dry_run
        )

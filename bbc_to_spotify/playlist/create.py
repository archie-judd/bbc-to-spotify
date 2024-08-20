import logging

from bbc_to_spotify.authorize.models.internal import Credentials
from bbc_to_spotify.playlist.utils import (
    Station,
    add_tracks_to_playlist,
    scrape_tracks_and_get_from_spotify,
)
from bbc_to_spotify.spotify.models.internal import Playlist, User
from bbc_to_spotify.spotify.spotify import Spotify

logger = logging.getLogger(__name__)


def get_user(spotify_client: Spotify) -> User:
    user_model = spotify_client.get_current_user_profile()
    user = User.from_external(user_model)
    return user


def create_playlist(
    spotify_client: Spotify,
    user_id: str,
    playlist_name: str,
    public: bool,
    description: str,
    dry_run: bool,
) -> Playlist:

    logger.info(f"Creating playlist {playlist_name}.")

    if not dry_run:
        playlist_model = spotify_client.create_playlist(
            user_id=user_id,
            playlist_name=playlist_name,
            public=public,
            description=description,
        )
        playlist = Playlist.from_external(playlist_model)
    else:
        playlist = Playlist(
            tracks=[],
            collaborative=False,
            description=description,
            name=playlist_name,
            public=public,
            uri="",
            id="",
        )
        logger.info(f"No playlist created (dry run)")

    return playlist


def create_playlist_and_add_tracks(
    credentials: Credentials,
    source: Station,
    playlist_name: str,
    private: bool,
    description: str,
    dry_run: bool,
) -> Playlist:

    spotify_client = Spotify(
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        grant_type="refresh_token",
        refresh_token=credentials.refresh_token,
    )

    source_tracks = scrape_tracks_and_get_from_spotify(
        spotify_client=spotify_client, station=source
    )

    user = get_user(spotify_client=spotify_client)

    dest_playlist = create_playlist(
        spotify_client=spotify_client,
        user_id=user.id,
        playlist_name=playlist_name,
        public=not private,
        description=description,
        dry_run=dry_run,
    )

    add_tracks_to_playlist(
        spotify_client=spotify_client,
        playlist_id=dest_playlist.id,
        dest_tracks=dest_playlist.tracks,
        source_tracks=source_tracks,
        remove_duplicates=False,
        dry_run=dry_run,
    )

    dest_playlist.tracks = source_tracks

    return dest_playlist

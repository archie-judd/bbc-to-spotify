import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler

from bbc_to_spotify.authorize.authorize import authorize, maybe_get_credentials
from bbc_to_spotify.cli import setup_parser
from bbc_to_spotify.playlist.create import create_playlist_and_add_tracks
from bbc_to_spotify.playlist.update import update_playlist
from bbc_to_spotify.utils import get_log_level_for_verbosity

logger = logging.getLogger(__name__)


def setup_logging(level: int, filename: str | None = None):

    handlers = []
    if filename:
        # Max log file size of 1MB, backing up 5 before deletion
        file_handler = RotatingFileHandler(
            filename, mode="a", maxBytes=1024 * 1024, backupCount=5
        )
        handlers.append(file_handler)

    else:
        stream_handler = StreamHandler()
        handlers.append(stream_handler)

    logging.basicConfig(
        handlers=handlers,
        level=level,
        format="%(asctime)s: %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S %Z",
    )


def main():

    try:

        parser = setup_parser()
        args = parser.parse_args()

        verbosity = args.verbose - args.quiet

        log_level = get_log_level_for_verbosity(verbosity)

        setup_logging(level=log_level, filename=args.log_file)

        logger.debug(f"Running with args: {vars(args)}")

        if args.command == "authorize":
            authorize(redirect_uri=args.redirect_uri)
        elif args.command == "create-playlist":
            credentials = maybe_get_credentials()
            if credentials is None:
                print(
                    "No credentials found, run 'bbc-to-spotify authorize' to generate "
                    "credentials, or alternatively set the environment variables "
                    "SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REFRESH_TOKEN."
                )
            else:
                playlist = create_playlist_and_add_tracks(
                    credentials=credentials,
                    source=args.source,
                    playlist_name=args.name,
                    private=args.private,
                    description=args.desc,
                    dry_run=args.dry_run,
                )
                if not args.dry_run:
                    print(
                        f"New playlist successfully created. Its playlist ID is: {playlist.id}"
                    )
                else:
                    print("Playlist not created (dry run).")
        elif args.command == "update-playlist":
            credentials = maybe_get_credentials()
            if credentials is None:
                print(
                    "No credentials found, run 'bbc-to-spotify authorize' to generate "
                    "credentials, or alternatively set the environment variables "
                    "SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REFRESH_TOKEN."
                )
            else:
                update_playlist(
                    credentials=credentials,
                    playlist_id=args.playlist_id,
                    source=args.source,
                    remove_duplicates=args.no_dups,
                    prune_dest=args.prune,
                    prepend=args.prepend,
                    update_description=args.update_desc,
                    dry_run=args.dry_run,
                )
                if not args.dry_run:
                    print(f"Playlist successfully updated.")
                else:
                    print("Playlist not updated (dry run).")

        logger.info("Done")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")

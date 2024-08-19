import logging

from bbc_to_spotify.authorize import authorize, maybe_get_credentials
from bbc_to_spotify.cli import setup_parser
from bbc_to_spotify.playlist.create import create_playlist_and_add_tracks
from bbc_to_spotify.playlist.update import update_playlist
from bbc_to_spotify.utils import get_log_level_for_verbosity


def main():

    parser = setup_parser()
    args = parser.parse_args()

    verbosity = args.verbose - args.quiet

    log_level = get_log_level_for_verbosity(verbosity)

    logging.basicConfig(
        filename=args.log_file,
        level=log_level,
        format="%(asctime)s: %(name)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S %Z",
    )

    logging.debug(f"Running with args: {vars(args)}")

    if args.command == "authorize":
        authorize(redirect_uri=args.redirect_uri)
    else:
        credentials = maybe_get_credentials()
        if credentials is None:
            print(
                "No credentials found, run 'bbc-to-spotify authorize' to generate "
                "credentials, or alternatively set the environment variables "
                "SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REFRESH_TOKEN."
            )
        elif args.command == "create-playlist":
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
                    f"New playlist successfully created. It's playlist ID is: {playlist.id}"
                )
            else:
                print("Playlist not created (dry run).")
        elif args.command == "update-playlist":
            update_playlist(
                credentials=credentials,
                playlist_id=args.playlist_id,
                source=args.source,
                remove_duplicates=args.no_dups,
                prune_dest=args.prune,
                update_description=args.update_desc,
                dry_run=args.dry_run,
            )
            if not args.dry_run:
                print(f"Playlist successfully updated.")
            else:
                print("Playlist not updated (dry run).")

    logging.info("Done")
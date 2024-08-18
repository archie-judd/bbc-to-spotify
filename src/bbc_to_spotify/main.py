import logging

from bbc_to_spotify.authorize import authorize, maybe_get_credentials
from bbc_to_spotify.cli import setup_parser
from bbc_to_spotify.sync import sync


def get_log_level_for_verbosity(verbosity: int) -> int:

    if verbosity <= -2:
        log_level = logging.CRITICAL
    elif verbosity == -1:
        log_level = logging.ERROR
    elif verbosity == 0:
        log_level = logging.WARNING
    elif verbosity == 1:
        log_level = logging.INFO
    elif verbosity >= 2:
        log_level = logging.DEBUG
    else:
        assert False, "unreachable"

    return log_level


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
    elif args.command == "sync":
        credentials = maybe_get_credentials()
        if credentials is None:
            print(
                "No credentials found, run 'bbc-to-spotify authorize' to generate "
                "credentials, or alternatively set the environment variables "
                "SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REFRESH_TOKEN."
            )
        else:
            sync(
                credentials=credentials,
                playlist_id=args.playlist_id,
                source=args.source,
                remove_duplicates=args.no_dups,
                prune_dest=args.prune,
                update_description=args.update_desc,
                dry_run=args.dry_run,
            )

    logging.info("Done")

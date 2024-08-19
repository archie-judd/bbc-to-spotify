import argparse
from argparse import ArgumentParser

from bbc_to_spotify import __project_name__, __version__
from bbc_to_spotify.authorize.authorize import REDIRECT_URI
from bbc_to_spotify.utils import Station

SOURCES: list[Station] = [
    "radio-1",
    "radio-1-xtra",
    "radio-2",
    "radio-6",
    "bbc-asian-network",
]


def setup_parser() -> ArgumentParser:
    root_parser = argparse.ArgumentParser(
        prog=__project_name__,
        description=(
            "A CLI tool for adding the BBC radio playlist tracks to Spotify playlists."
        ),
        add_help=True,
    )
    root_parser.add_argument(
        "--version", "-V", action="version", version=f"{__project_name__} {__version__}"
    )

    logging_parser = argparse.ArgumentParser(add_help=False)
    logging_parser.add_argument(
        "--verbose",
        "-v",
        help="Increase logging verbosity (-vv to increase further).",
        action="count",
        default=0,
    )
    logging_parser.add_argument(
        "--quiet",
        "-q",
        help="Decrease logging verbosity (-qq to decrease further).",
        action="count",
        default=0,
    )
    logging_parser.add_argument(
        "--log-file",
        "-l",
        help="Write logs to this file. Suppresses logging in stdout.",
        required=False,
        default=None,
        type=str,
    )

    command_parsers = root_parser.add_subparsers(
        title="commands", dest="command", required=True
    )
    update_parser = command_parsers.add_parser(
        "update-playlist",
        add_help=True,
        parents=[logging_parser],
        description="Create a new Spotify playlist with songs from a BBC radio station's current playlist.",
    )
    create_parser = command_parsers.add_parser(
        "create-playlist",
        add_help=True,
        parents=[logging_parser],
        description="Update an existing Spotify playlist with songs from a BBC radio station's current playlist.",
    )

    update_parser.add_argument(
        "playlist_id",
        metavar="playlist-id",
        help=(
            "The ID of the Spotify playlist on which to add the BBC station's current"
            " playlist tracks."
        ),
        type=str,
    )
    update_parser.add_argument(
        "source",
        help=(
            "The BBC Radio station whose current playlist should be added to the"
            f" Spotify playlist. Possible values: {SOURCES}"
        ),
        choices=SOURCES,
        metavar="source",
        type=str,
    )
    update_parser.add_argument(
        "--prune",
        "-p",
        help=(
            "Remove all duplicates and any tracks that are not in the source playlist."
        ),
        required=False,
        action="store_true",
    )
    update_parser.add_argument(
        "--no-dups",
        "-N",
        help="Only add tracks that are not already in the destination playlist.",
        required=False,
        action="store_true",
    )
    update_parser.add_argument(
        "--update-desc",
        "-u",
        help="Add a 'Last updated' timestamp to the destination playlist desription.",
        required=False,
        action="store_true",
    )
    update_parser.add_argument(
        "--dry-run",
        "-n",
        help="Run the command but do not update the destination playlist.",
        required=False,
        action="store_true",
    )

    create_parser.add_argument(
        "name",
        help="The name of the playlist to be created.",
    )
    create_parser.add_argument(
        "source",
        help=(
            "The BBC Radio station whose current playlist should be added to the"
            f" Spotify playlist. Possible values: {SOURCES}"
        ),
        choices=SOURCES,
        metavar="source",
        type=str,
    )
    create_parser.add_argument(
        "--private",
        "-p",
        help="Make the playlist private rather than public.",
        required=False,
        action="store_true",
    )
    create_parser.add_argument(
        "--desc",
        help="Run the command but do not create the playlist.",
        required=False,
        default=None,
        type=str,
    )
    create_parser.add_argument(
        "--dry-run",
        "-n",
        help="Run the update command but do not create the playlist.",
        required=False,
        action="store_true",
    )

    auth_parser = command_parsers.add_parser(
        "authorize", add_help=True, parents=[logging_parser]
    )
    auth_parser.add_argument(
        "--redirect-uri",
        help=(
            f"Redirect URI to use during authorization. Default value is"
            f" `http://localhost:8080/bbc-to-spotify`"
        ),
        required=False,
        default=REDIRECT_URI,
        type=str,
    )
    return root_parser

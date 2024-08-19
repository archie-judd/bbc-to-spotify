import logging
from typing import Any, Literal, Union

Station = Union[
    Literal["radio-1"],
    Literal["radio-1-xtra"],
    Literal["radio-2"],
    Literal["radio-6"],
    Literal["bbc-asian-network"],
]


PlaylistUrl = Union[
    Literal[
        "https://www.bbc.co.uk/programmes/articles/3tqPdBWF9yMbTrfjWvfKV8t/radio-1-playlist"
    ],
    Literal[
        "https://www.bbc.co.uk/programmes/articles/2sgpCPqVPgjqC7tHBb97kd9/the-1xtra-playlist"
    ],
    Literal[
        "https://www.bbc.co.uk/programmes/articles/2qNJsnjYFvbLrK9CZ0CfYfM/radio-2-new-music-playlist"
    ],
    Literal[
        "https://www.bbc.co.uk/programmes/articles/5JDPyPdDGs3yCLdtPhGgWM7/bbc-radio-6-music-playlist"
    ],
    Literal[
        "https://www.bbc.co.uk/programmes/articles/z39bpDGcLXC9Sy64yz1Xgt/asian-network-playlist"
    ],
]


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


def get_playlist_url(station: Station) -> PlaylistUrl:

    match station:
        case "radio-1":
            playlist_url = "https://www.bbc.co.uk/programmes/articles/3tqPdBWF9yMbTrfjWvfKV8t/radio-1-playlist"
        case "radio-1-xtra":
            playlist_url = "https://www.bbc.co.uk/programmes/articles/2sgpCPqVPgjqC7tHBb97kd9/the-1xtra-playlist"
        case "radio-2":
            playlist_url = "https://www.bbc.co.uk/programmes/articles/2qNJsnjYFvbLrK9CZ0CfYfM/radio-2-new-music-playlist"
        case "radio-6":
            playlist_url = "https://www.bbc.co.uk/programmes/articles/5JDPyPdDGs3yCLdtPhGgWM7/bbc-radio-6-music-playlist"
        case "bbc-asian-network":
            playlist_url = "https://www.bbc.co.uk/programmes/articles/z39bpDGcLXC9Sy64yz1Xgt/asian-network-playlist"

    return playlist_url


def batch_list(l: list[Any], batch_size: int) -> list[list[Any]]:

    batches = []
    num_items = len(l)

    for idx_start in range(0, num_items, batch_size):
        idx_end = min([num_items, idx_start + batch_size])
        batches.append(l[idx_start:idx_end])

    return batches

from typing import Literal, Union

Station = Union[
    Literal["radio-1"],
    Literal["radio-1-xtra"],
    Literal["radio-2"],
    Literal["radio-6"],
    Literal["bbc-asian-network"],
]


class PlaylistURL(str):
    pass


def get_playlist_url(station: Station) -> PlaylistURL:

    match station:
        case "radio-1":
            playlist_url = "https://www.bbc.co.uk/programmes/articles/3tqPdBWF9yMbTrfjWvfKV8t/radio-1-playlist"
        case "radio-1-xtra":
            playlist_url = ""
        case "radio-2":
            playlist_url = ""
        case "radio-6":
            playlist_url = "https://www.bbc.co.uk/programmes/articles/5JDPyPdDGs3yCLdtPhGgWM7/bbc-radio-6-music-playlist"
        case "radio-6":
            playlist_url = ""
        case "bbc-asian-network":
            playlist_url = ""

    playlist_url = PlaylistURL(playlist_url)

    return playlist_url

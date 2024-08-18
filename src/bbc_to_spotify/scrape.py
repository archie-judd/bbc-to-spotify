import logging
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup as bs
from bs4.element import NavigableString, Tag

from bbc_to_spotify.station import PlaylistURL


@dataclass
class ScrapedTrack:
    name: str
    artist: str


def scrape_primary_artist(artist: str) -> str:
    artist_primary = artist.replace("&", "ft.").split("ft.")[0]
    return artist_primary


def scrape_all_navigable_strings_in_tag(tag: Tag) -> list[NavigableString]:
    strings = []
    for child in tag.children:
        if isinstance(child, Tag):
            child_strings = scrape_all_navigable_strings_in_tag(tag=child)
            strings.extend(child_strings)
        elif isinstance(child, NavigableString):
            strings.append(child)
    return strings


def scrape_tracks_in_para(para: Tag) -> list[ScrapedTrack]:
    scraped_tracks: list[ScrapedTrack] = []
    logging.debug("Collecting navigable strings.")
    navigable_strings = scrape_all_navigable_strings_in_tag(tag=para)
    for navigable_string in navigable_strings:
        logging.info(f"Scraping navigable string: {navigable_string}")
        artist = navigable_string.text.split(" - ")[0]
        primary_artist = scrape_primary_artist(artist)
        track_name = navigable_string.text.split(" - ")[-1]
        scraped_tracks.append(ScrapedTrack(artist=primary_artist, name=track_name))
    return scraped_tracks


def scrape_tracks_in_section(section: Tag) -> list[ScrapedTrack]:
    scraped_tracks = []
    paras = section.find_all("p")
    for para in paras:
        logging.debug(f"Scraping para: {para}")
        para_tracks = scrape_tracks_in_para(para=para)
        scraped_tracks.extend(para_tracks)
    return scraped_tracks


def scrape_tracks_from_playlist_page(playlist_url: PlaylistURL) -> list[ScrapedTrack]:

    scraped_tracks: list[ScrapedTrack] = []

    logging.info(f"Scraping tracks from:{playlist_url}")

    page = requests.get(url=playlist_url, timeout=30)
    soup = bs(markup=page.content, features="html.parser")

    sections = soup.find_all(
        class_=(
            "component component--box component--box-flushbody-vertical"
            " component--box--primary"
        )
    )
    for section in sections:

        headers: list[Tag] = section.find_all("h2")

        if not headers:
            continue
        header = headers[0].text.strip()

        if header.endswith("LIST"):
            logging.debug(f"Scraping '*-LIST' section: {section}")
            section_tracks = scrape_tracks_in_section(section=section)
            scraped_tracks.extend(section_tracks)

    logging.debug(f"Scraped {len(scraped_tracks)} tracks.\n{scraped_tracks}")

    return scraped_tracks

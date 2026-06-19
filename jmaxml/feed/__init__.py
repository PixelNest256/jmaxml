"""JMAXML Feed Client - fetches Atom feeds from JMA."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.request import urlopen, Request
from urllib.error import URLError
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

ATOM_NS = "http://www.w3.org/2005/Atom"

FEED_URLS = {
    "earthquake": "https://www.data.jma.go.jp/developer/xml/feed/eqvol.xml",
    "weather": "https://www.data.jma.go.jp/developer/xml/feed/extra.xml",
    "regular": "https://www.data.jma.go.jp/developer/xml/feed/regular.xml",
    "other": "https://www.data.jma.go.jp/developer/xml/feed/other.xml",
    "all": "https://www.data.jma.go.jp/developer/xml/feed/extra_l.xml",
}


@dataclass
class FeedEntry:
    title: str
    link: str
    updated: str
    content: str

    def __repr__(self) -> str:
        return f"<FeedEntry title={self.title!r}>"


class FeedClient:
    """Fetch Atom feeds from JMA.

    Usage:
        client = FeedClient()
        entries = client.fetch_feed("earthquake")
    """

    def __init__(self, user_agent: str = "jmaxml-sdk/1.0") -> None:
        self.user_agent = user_agent

    def fetch_feed(self, feed_type: str = "earthquake") -> list[FeedEntry]:
        if feed_type not in FEED_URLS:
            raise ValueError(f"Unknown feed type: {feed_type}. Available: {list(FEED_URLS.keys())}")

        url = FEED_URLS[feed_type]
        entries: list[FeedEntry] = []

        try:
            req = Request(url, headers={"User-Agent": self.user_agent})
            with urlopen(req, timeout=30) as response:
                xml_data = response.read()

            root = ET.fromstring(xml_data)
            for entry in root.findall(f"{{{ATOM_NS}}}entry"):
                title = ""
                link = ""
                updated = ""
                content = ""

                title_elem = entry.find(f"{{{ATOM_NS}}}title")
                if title_elem is not None and title_elem.text:
                    title = title_elem.text.strip()

                link_elem = entry.find(f"{{{ATOM_NS}}}link")
                if link_elem is not None:
                    link = link_elem.get("href", "")

                updated_elem = entry.find(f"{{{ATOM_NS}}}updated")
                if updated_elem is not None and updated_elem.text:
                    updated = updated_elem.text.strip()

                content_elem = entry.find(f"{{{ATOM_NS}}}content")
                if content_elem is not None and content_elem.text:
                    content = content_elem.text.strip()

                entries.append(FeedEntry(
                    title=title,
                    link=link,
                    updated=updated,
                    content=content,
                ))
        except URLError as e:
            logger.error("Failed to fetch feed from %s: %s", url, e)
        except ET.ParseError as e:
            logger.error("Failed to parse feed XML from %s: %s", url, e)

        return entries

    def fetch_xml(self, url: str) -> str:
        req = Request(url, headers={"User-Agent": self.user_agent})
        with urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8")

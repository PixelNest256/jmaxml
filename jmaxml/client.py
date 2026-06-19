"""JMAXML Client - main entry point for the SDK."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import AsyncIterator, Iterator

from jmaxml.feed import FeedClient, FeedEntry
from jmaxml.feed.watcher import Watcher, AsyncWatcher
from jmaxml.models import BaseReport, ReportType
from jmaxml.parser import parse
from jmaxml.storage import SqliteStorage

logger = logging.getLogger(__name__)


class Client:
    """JMAXML SDK client.

    Usage:
        client = Client()
        reports = client.fetch_recent()
    """

    def __init__(self, user_agent: str = "jmaxml-sdk/1.0") -> None:
        self.feed_client = FeedClient(user_agent=user_agent)
        self._storage: SqliteStorage | None = None

    def enable_storage(self, db_path: str = "jmaxml_reports.db") -> None:
        self._storage = SqliteStorage(db_path)

    def fetch_feed(self, feed_type: str = "earthquake") -> list[FeedEntry]:
        return self.feed_client.fetch_feed(feed_type)

    def fetch_latest(self, feed_type: str = "earthquake") -> list[BaseReport]:
        entries = self.feed_client.fetch_feed(feed_type)
        reports: list[BaseReport] = []

        for entry in entries[:10]:
            try:
                xml_data = self.feed_client.fetch_xml(entry.link)
                report = parse(xml_data)
                reports.append(report)
                if self._storage:
                    self._storage.save(report)
            except Exception as e:
                logger.debug("Failed to fetch report %s: %s", entry.link, e)
                continue

        return reports

    def fetch_recent(
        self,
        hours: int = 24,
        report_type: str | None = None,
    ) -> list[BaseReport]:
        if self._storage:
            start_date = datetime.now() - timedelta(hours=hours)
            return self._storage.search(
                start_date=start_date,
                report_type=report_type,
            )

        feed_type = report_type or "earthquake"
        entries = self.feed_client.fetch_feed(feed_type)
        reports: list[BaseReport] = []

        for entry in entries:
            try:
                xml_data = self.feed_client.fetch_xml(entry.link)
                report = parse(xml_data)
                reports.append(report)
            except Exception as e:
                logger.debug("Failed to fetch report %s: %s", entry.link, e)
                continue

        return reports

    def get_event(self, event_id: str) -> BaseReport | None:
        if self._storage:
            return self._storage.get(event_id)

        for feed_type in ["earthquake", "weather", "regular"]:
            entries = self.feed_client.fetch_feed(feed_type)
            for entry in entries:
                if event_id in entry.link:
                    try:
                        xml_data = self.feed_client.fetch_xml(entry.link)
                        return parse(xml_data)
                    except Exception as e:
                        logger.debug("Failed to fetch report %s: %s", entry.link, e)
                        continue

        return None

    def download(self, entry: FeedEntry) -> str:
        return self.feed_client.fetch_xml(entry.link)

    def watch(self, feed_type: str = "earthquake", interval: int = 60) -> Iterator[BaseReport]:
        watcher = Watcher(feed_type=feed_type, interval=interval)
        yield from watcher.watch()

    async def awatch(self, feed_type: str = "earthquake", interval: int = 60) -> AsyncIterator[BaseReport]:
        watcher = AsyncWatcher(feed_type=feed_type, interval=interval)
        async for report in watcher.watch():
            yield report

    def search(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        report_type: str | None = None,
    ) -> list[BaseReport]:
        if not self._storage:
            raise RuntimeError("Storage not enabled. Call client.enable_storage() first.")

        return self._storage.search(
            start_date=start_date,
            end_date=end_date,
            report_type=report_type,
        )

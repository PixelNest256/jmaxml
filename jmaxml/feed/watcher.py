"""JMAXML Watcher - monitors JMA feeds for new reports."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Iterator

from jmaxml.feed import FeedClient
from jmaxml.models import BaseReport
from jmaxml.parser import parse


class Watcher:
    """Watch JMA feeds for new reports.

    Usage:
        watcher = Watcher()
        for report in watcher.watch():
            print(report.title)
    """

    def __init__(self, feed_type: str = "earthquake", interval: int = 60) -> None:
        self.feed_client = FeedClient()
        self.feed_type = feed_type
        self.interval = interval
        self._seen_ids: set[str] = set()

    def fetch_new_reports(self) -> list[BaseReport]:
        entries = self.feed_client.fetch_feed(self.feed_type)
        reports: list[BaseReport] = []

        for entry in entries:
            if entry.link in self._seen_ids:
                continue

            self._seen_ids.add(entry.link)

            try:
                xml_data = self.feed_client.fetch_xml(entry.link)
                report = parse(xml_data)
                reports.append(report)
            except Exception:
                continue

        return reports

    def watch(self) -> Iterator[BaseReport]:
        """Watch for new reports. Yields reports as they arrive."""
        import time

        while True:
            reports = self.fetch_new_reports()
            for report in reports:
                yield report
            time.sleep(self.interval)


class AsyncWatcher:
    """Async watch JMA feeds for new reports.

    Usage:
        watcher = AsyncWatcher()
        async for report in watcher.watch():
            print(report.title)
    """

    def __init__(self, feed_type: str = "earthquake", interval: int = 60) -> None:
        self.feed_client = FeedClient()
        self.feed_type = feed_type
        self.interval = interval
        self._seen_ids: set[str] = set()

    async def fetch_new_reports(self) -> list[BaseReport]:
        entries = await asyncio.to_thread(self.feed_client.fetch_feed, self.feed_type)
        reports: list[BaseReport] = []

        for entry in entries:
            if entry.link in self._seen_ids:
                continue

            self._seen_ids.add(entry.link)

            try:
                xml_data = await asyncio.to_thread(self.feed_client.fetch_xml, entry.link)
                report = parse(xml_data)
                reports.append(report)
            except Exception:
                continue

        return reports

    async def watch(self) -> AsyncIterator[BaseReport]:
        """Watch for new reports. Yields reports as they arrive."""
        while True:
            reports = await self.fetch_new_reports()
            for report in reports:
                yield report
            await asyncio.sleep(self.interval)

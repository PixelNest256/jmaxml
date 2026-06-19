"""Tests for JMAXML SDK."""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from jmaxml import (
    Client,
    parse,
    FeedClient,
    FeedEntry,
    Watcher,
    AsyncWatcher,
    BaseReport,
    EarthquakeReport,
    TsunamiReport,
    WeatherWarningReport,
    ReportType,
    Area,
    TsunamiArea,
    Warning,
    SqliteStorage,
)


# Real JMA XML samples
REAL_EARTHQUAKE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://xml.kishou.go.jp/jmaxml1/">
<Control>
<Title>震源・震度に関する情報</Title>
<DateTime>2026-06-18T22:36:29Z</DateTime>
<Status>通常</Status>
<EditorialOffice>気象庁本庁</EditorialOffice>
<PublishingOffice>気象庁</PublishingOffice>
</Control>
<Head xmlns="http://xml.kishou.go.jp/jmaxml1/informationBasis1/">
<Title>震源・震度情報</Title>
<ReportDateTime>2026-06-19T07:36:00+09:00</ReportDateTime>
<EventID>20260619073313</EventID>
<InfoType>発表</InfoType>
<Serial>1</Serial>
<InfoKind>地震情報</InfoKind>
<InfoKindVersion>1.0_1</InfoKindVersion>
</Head>
<Body xmlns="http://xml.kishou.go.jp/jmaxml1/body/seismology1/" xmlns:jmx_eb="http://xml.kishou.go.jp/jmaxml1/elementBasis1/">
<Earthquake>
<OriginTime>2026-06-19T07:33:00+09:00</OriginTime>
<Hypocenter>
<Area>
<Name>福島県沖</Name>
<Code>289</Code>
</Area>
</Hypocenter>
<jmx_eb:Magnitude type="Mj">4.1</jmx_eb:Magnitude>
</Earthquake>
<Intensity>
<Observation>
<MaxInt>1</MaxInt>
<Pref><Name>福島県</Name><MaxInt>1</MaxInt>
<Area><Name>福島県中通り</Name><MaxInt>1</MaxInt></Area>
<Area><Name>福島県浜通り</Name><MaxInt>1</MaxInt></Area>
</Pref>
</Observation>
</Intensity>
</Body>
</Report>
"""

REAL_INTENSITY_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://xml.kishou.go.jp/jmaxml1/">
<Control>
<Title>震度速報</Title>
<DateTime>2026-06-18T22:36:29Z</DateTime>
<Status>通常</Status>
<EditorialOffice>気象庁本庁</EditorialOffice>
<PublishingOffice>気象庁</PublishingOffice>
</Control>
<Head xmlns="http://xml.kishou.go.jp/jmaxml1/informationBasis1/">
<Title>震度速報</Title>
<ReportDateTime>2026-06-19T07:36:00+09:00</ReportDateTime>
<EventID>20260619073313</EventID>
<InfoType>発表</InfoType>
<Serial>1</Serial>
<InfoKind>震度速報</InfoKind>
<InfoKindVersion>1.0_1</InfoKindVersion>
</Head>
<Body xmlns="http://xml.kishou.go.jp/jmaxml1/body/seismology1/">
<Intensity>
<Observation>
<MaxInt>5弱</MaxInt>
<Pref><Name>福島県</Name><MaxInt>5弱</MaxInt>
<Area><Name>福島県中通り</Name><MaxInt>5弱</MaxInt></Area>
</Pref>
<Pref><Name>宮城県</Name><MaxInt>4</MaxInt>
<Area><Name>宮城県南部</Name><MaxInt>4</MaxInt></Area>
</Pref>
</Observation>
</Intensity>
</Body>
</Report>
"""


# Parser tests
class TestParse:
    def test_parse_earthquake(self) -> None:
        report = parse(REAL_EARTHQUAKE_XML)
        assert isinstance(report, EarthquakeReport)
        assert report.epicenter == "福島県沖"
        assert report.magnitude == 4.1
        assert report.max_intensity == "1"
        assert len(report.areas) == 2

    def test_parse_intensity(self) -> None:
        report = parse(REAL_INTENSITY_XML)
        assert isinstance(report, EarthquakeReport)
        assert report.max_intensity == "5弱"
        assert len(report.areas) == 2
        assert report.areas[0].name == "福島県中通り"
        assert report.areas[0].intensity == "5弱"

    def test_to_json(self) -> None:
        report = parse(REAL_EARTHQUAKE_XML)
        json_str = report.to_json()
        data = json.loads(json_str)
        assert data["title"] == "震源・震度に関する情報"
        assert data["epicenter"] == "福島県沖"
        assert data["magnitude"] == 4.1
        assert data["report_type"] == "earthquake"

    def test_to_dict(self) -> None:
        report = parse(REAL_EARTHQUAKE_XML)
        d = report.to_dict()
        assert "title" in d
        assert "event_id" in d
        assert "report_datetime" in d
        assert "epicenter" in d


# FeedClient tests
class TestFeedClient:
    def test_fetch_feed(self) -> None:
        client = FeedClient()
        entries = client.fetch_feed("earthquake")
        assert isinstance(entries, list)
        assert len(entries) > 0
        assert entries[0].title != ""
        assert entries[0].link != ""


# Watcher tests
class TestWatcher:
    def test_fetch_new_reports(self) -> None:
        watcher = Watcher("earthquake")
        reports = watcher.fetch_new_reports()
        assert isinstance(reports, list)
        assert len(reports) > 0
        assert hasattr(reports[0], "title")


# Client tests
class TestClient:
    def test_fetch_latest(self) -> None:
        client = Client()
        mock_entry = FeedEntry(
            title="震源・震度に関する情報",
            link="https://example.com/eq.xml",
            updated="2026-06-19T07:36:00Z",
            content="",
        )
        with patch.object(client.feed_client, "fetch_feed", return_value=[mock_entry]):
            with patch.object(client.feed_client, "fetch_xml", return_value=REAL_EARTHQUAKE_XML):
                reports = client.fetch_latest("earthquake")
        assert isinstance(reports, list)
        assert len(reports) == 1
        assert isinstance(reports[0], EarthquakeReport)

    def test_client_with_storage(self, tmp_path) -> None:
        client = Client()
        db_path = str(tmp_path / "test.db")
        client.enable_storage(db_path)

        report = parse(REAL_EARTHQUAKE_XML)
        client._storage.save(report)

        retrieved = client._storage.get(report.event_id)
        assert retrieved is not None
        assert retrieved.event_id == report.event_id


# Storage tests
class TestStorage:
    def test_save_and_get(self, tmp_path) -> None:
        db_path = str(tmp_path / "test.db")
        storage = SqliteStorage(db_path)

        report = parse(REAL_EARTHQUAKE_XML)
        storage.save(report)

        retrieved = storage.get(report.event_id)
        assert retrieved is not None
        assert retrieved.event_id == report.event_id
        assert retrieved.title == report.title

    def test_search(self, tmp_path) -> None:
        db_path = str(tmp_path / "test.db")
        storage = SqliteStorage(db_path)

        report = parse(REAL_EARTHQUAKE_XML)
        storage.save(report)

        reports = storage.search()
        assert len(reports) == 1

    def test_count(self, tmp_path) -> None:
        db_path = str(tmp_path / "test.db")
        storage = SqliteStorage(db_path)

        report = parse(REAL_EARTHQUAKE_XML)
        storage.save(report)

        assert storage.count() == 1

    def test_delete(self, tmp_path) -> None:
        db_path = str(tmp_path / "test.db")
        storage = SqliteStorage(db_path)

        report = parse(REAL_EARTHQUAKE_XML)
        storage.save(report)

        assert storage.delete(report.event_id)
        assert storage.count() == 0

    def test_clear(self, tmp_path) -> None:
        db_path = str(tmp_path / "test.db")
        storage = SqliteStorage(db_path)

        report = parse(REAL_EARTHQUAKE_XML)
        storage.save(report)

        cleared = storage.clear()
        assert cleared == 1
        assert storage.count() == 0


# AsyncWatcher tests
class TestAsyncWatcher:
    def test_init(self) -> None:
        watcher = AsyncWatcher("earthquake")
        assert watcher.feed_type == "earthquake"

"""Tests for new features: pandas, geojson, notify, fastapi."""

import json
import pytest
from datetime import datetime

from jmaxml import (
    parse,
    to_dataframe,
    reports_to_dataframe,
    to_geojson,
    to_geojson_collection,
    notify,
    check_report,
    BaseReport,
    EarthquakeReport,
    TsunamiReport,
    WeatherWarningReport,
    Warning,
    ReportType,
)


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
</Pref>
</Observation>
</Intensity>
</Body>
</Report>
"""


class TestPandasIntegration:
    def test_to_dataframe(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not installed")

        report = parse(REAL_EARTHQUAKE_XML)
        df = to_dataframe(report)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "epicenter" in df.columns
        assert "magnitude" in df.columns

    def test_reports_to_dataframe(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not installed")

        report = parse(REAL_EARTHQUAKE_XML)
        df = reports_to_dataframe([report])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1


class TestGeoJSON:
    def test_to_geojson(self) -> None:
        report = parse(REAL_EARTHQUAKE_XML)
        geojson = to_geojson(report)
        assert geojson["type"] == "Feature"
        assert "geometry" in geojson
        assert "properties" in geojson
        assert geojson["properties"]["epicenter"] == "福島県沖"
        assert geojson["properties"]["magnitude"] == 4.1

    def test_to_geojson_collection(self) -> None:
        report = parse(REAL_EARTHQUAKE_XML)
        geojson = to_geojson_collection([report])
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 1
        assert geojson["features"][0]["properties"]["epicenter"] == "福島県沖"


class TestNotify:
    def test_check_report_earthquake(self) -> None:
        report = parse(REAL_EARTHQUAKE_XML)
        assert not check_report(report)

    def test_check_report_high_intensity(self) -> None:
        report = EarthquakeReport(
            title="テスト",
            event_id="test",
            report_datetime=datetime.now(),
            epicenter="テスト",
            magnitude=7.0,
            max_intensity="6強",
        )
        assert check_report(report)

    def test_check_report_tsunami(self) -> None:
        report = TsunamiReport(
            title="テスト",
            event_id="test",
            report_datetime=datetime.now(),
            warning_level="津波警報",
        )
        assert check_report(report)

    def test_check_report_warning(self) -> None:
        report = WeatherWarningReport(
            title="テスト",
            event_id="test",
            report_datetime=datetime.now(),
            warnings=[Warning(name="暴風警報", area="東京都")],
        )
        assert check_report(report)

    def test_notify_returns_bool(self) -> None:
        report = parse(REAL_EARTHQUAKE_XML)
        result = notify(report, title="テスト通知")
        assert isinstance(result, bool)


class TestFastAPI:
    def test_create_app(self) -> None:
        try:
            from jmaxml.fastapi_app import create_app
        except ImportError:
            pytest.skip("fastapi not installed")

        app = create_app()
        assert app is not None
        assert app.title == "JMAXML API"

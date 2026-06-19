"""Comprehensive tests covering gaps in existing test suite."""

import json
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from jmaxml.models import (
    Area,
    BaseReport,
    EarthquakeReport,
    ReportType,
    TsunamiArea,
    TsunamiReport,
    Warning,
    WeatherWarningReport,
)
from jmaxml.parser import parse
from jmaxml.geojson import to_geojson, to_geojson_collection, _get_coords, PREFECTURE_COORDS
from jmaxml.notify import notify, check_report, _build_title, _build_body
from jmaxml.pandas import to_dataframe, reports_to_dataframe
from jmaxml.storage import SqliteStorage
from jmaxml.feed import FeedClient, FeedEntry
from jmaxml.feed.watcher import Watcher, AsyncWatcher
from jmaxml.client import Client


# ============================================================
# XML Samples
# ============================================================

TSUNAMI_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://xml.kishou.go.jp/jmaxml1/">
<Control>
<Title>津波警報・注意報・速報</Title>
<DateTime>2026-06-18T22:00:00Z</DateTime>
<Status>通常</Status>
<EditorialOffice>気象庁本庁</EditorialOffice>
<PublishingOffice>気象庁</PublishingOffice>
</Control>
<Head xmlns="http://xml.kishou.go.jp/jmaxml1/informationBasis1/">
<Title>津波警報</Title>
<ReportDateTime>2026-06-19T07:00:00+09:00</ReportDateTime>
<EventID>20260619070000</EventID>
<InfoType>発表</InfoType>
<Serial>1</Serial>
<InfoKind>津波警報</InfoKind>
<InfoKindVersion>1.0_1</InfoKindVersion>
</Head>
<Body xmlns="http://xml.kishou.go.jp/jmaxml1/body/seismology1/">
<Tsunami>
<Category>津波警報</Category>
<Area>
<Name>宮城県</Name>
<ArrivalTime>2026-06-19T08:00:00+09:00</ArrivalTime>
<Height>3m</Height>
<Category>津波警報</Category>
</Area>
<Area>
<Name>福島県</Name>
<ArrivalTime>2026-06-19T08:30:00+09:00</ArrivalTime>
<Height>2m</Height>
<Category>津波注意報</Category>
</Area>
</Tsunami>
</Body>
</Report>
"""

WEATHER_WARNING_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://xml.kishou.go.jp/jmaxml1/">
<Control>
<Title>暴風警報</Title>
<DateTime>2026-06-18T22:00:00Z</DateTime>
<Status>通常</Status>
<EditorialOffice>気象庁本庁</EditorialOffice>
<PublishingOffice>気象庁</PublishingOffice>
</Control>
<Head xmlns="http://xml.kishou.go.jp/jmaxml1/informationBasis1/">
<Title>暴風警報</Title>
<ReportDateTime>2026-06-19T07:00:00+09:00</ReportDateTime>
<EventID>20260619070001</EventID>
<InfoType>発表</InfoType>
<Serial>1</Serial>
<InfoKind>警報</InfoKind>
<InfoKindVersion>1.0_1</InfoKindVersion>
</Head>
<Body xmlns="http://xml.kishou.go.jp/jmaxml1/body/seismology1/">
<Warning>
<Area>
<Name>東京都</Name>
<Item>
<Name>暴風警報</Name>
</Item>
</Area>
<Area>
<Name>神奈川県</Name>
<Item>
<Name>大雨注意報</Name>
</Item>
</Area>
</Warning>
</Body>
</Report>
"""

SPECIAL_WARNING_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://xml.kishou.go.jp/jmaxml1/">
<Control>
<Title>大雨特別警報</Title>
<DateTime>2026-06-18T22:00:00Z</DateTime>
<Status>通常</Status>
<EditorialOffice>気象庁本庁</EditorialOffice>
<PublishingOffice>気象庁</PublishingOffice>
</Control>
<Head xmlns="http://xml.kishou.go.jp/jmaxml1/informationBasis1/">
<Title>大雨特別警報</Title>
<ReportDateTime>2026-06-19T07:00:00+09:00</ReportDateTime>
<EventID>20260619070002</EventID>
<InfoType>発表</InfoType>
<Serial>1</Serial>
<InfoKind>特別警報</InfoKind>
<InfoKindVersion>1.0_1</InfoKindVersion>
</Head>
<Body xmlns="http://xml.kishou.go.jp/jmaxml1/body/seismology1/">
<Warning>
<Area>
<Name>広島県</Name>
<Item>
<Name>大雨特別警報</Name>
</Item>
</Area>
</Warning>
</Body>
</Report>
"""

EARTHQUAKE_XML = """<?xml version="1.0" encoding="UTF-8"?>
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
<TargetDateTime>2026-06-19T08:00:00+09:00</TargetDateTime>
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

UNKNOWN_TYPE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://xml.kishou.go.jp/jmaxml1/">
<Control>
<Title>テスト情報</Title>
<DateTime>2026-06-18T22:00:00Z</DateTime>
<Status>通常</Status>
<EditorialOffice>気象庁本庁</EditorialOffice>
<PublishingOffice>気象庁</PublishingOffice>
</Control>
<Head xmlns="http://xml.kishou.go.jp/jmaxml1/informationBasis1/">
<Title>テスト情報</Title>
<ReportDateTime>2026-06-19T07:00:00+09:00</ReportDateTime>
<EventID>20260619070099</EventID>
<InfoType>発表</InfoType>
<Serial>1</Serial>
<InfoKind>テスト</InfoKind>
<InfoKindVersion>1.0_1</InfoKindVersion>
</Head>
<Body xmlns="http://xml.kishou.go.jp/jmaxml1/body/seismology1/">
</Body>
</Report>
"""


# ============================================================
# Tests: Models
# ============================================================

class TestModelsExtended:
    def test_base_report_repr(self) -> None:
        report = BaseReport(
            title="テスト",
            event_id="test123",
            report_datetime=datetime(2026, 1, 1),
        )
        assert repr(report) == "<BaseReport title='テスト'>"

    def test_base_report_to_dict_with_target_datetime(self) -> None:
        target = datetime(2026, 6, 19, 8, 0, 0)
        report = BaseReport(
            title="テスト",
            event_id="test123",
            report_datetime=datetime(2026, 6, 19, 7, 0),
            target_datetime=target,
        )
        d = report.to_dict()
        assert d["target_datetime"] == target.isoformat()

    def test_base_report_to_dict_without_target_datetime(self) -> None:
        report = BaseReport(
            title="テスト",
            event_id="test123",
            report_datetime=datetime(2026, 6, 19, 7, 0),
        )
        d = report.to_dict()
        assert "target_datetime" not in d or d.get("target_datetime") is None

    def test_base_report_to_json_indent(self) -> None:
        report = BaseReport(
            title="テスト",
            event_id="test123",
            report_datetime=datetime(2026, 6, 19, 7, 0),
        )
        json_str = report.to_json(indent=2)
        assert "\n" in json_str
        data = json.loads(json_str)
        assert data["title"] == "テスト"

    def test_base_report_report_type(self) -> None:
        report = BaseReport(
            title="テスト",
            event_id="test123",
            report_datetime=datetime.now(),
        )
        assert report.report_type == ReportType.UNKNOWN

    def test_earthquake_report_repr(self) -> None:
        report = EarthquakeReport(
            title="地震情報",
            event_id="eq123",
            report_datetime=datetime.now(),
            epicenter="福島県沖",
        )
        assert "EarthquakeReport" in repr(report)
        assert "地震情報" in repr(report)

    def test_tsunami_report_report_type(self) -> None:
        report = TsunamiReport(
            title="津波情報",
            event_id="ts123",
            report_datetime=datetime.now(),
            warning_level="津波警報",
        )
        assert report.report_type == ReportType.TSUNAMI

    def test_weather_warning_report_report_type(self) -> None:
        report = WeatherWarningReport(
            title="警報情報",
            event_id="ww123",
            report_datetime=datetime.now(),
            warnings=[Warning(name="暴風警報", area="東京都")],
        )
        assert report.report_type == ReportType.WEATHER_WARNING

    def test_tsunami_area_defaults(self) -> None:
        area = TsunamiArea(name="宮城県")
        assert area.first_wave_time == ""
        assert area.first_wave_height == ""
        assert area.category == ""

    def test_area_defaults(self) -> None:
        area = Area(name="テスト")
        assert area.intensity == ""

    def test_warning_defaults(self) -> None:
        w = Warning(name="暴風警報")
        assert w.area == ""

    def test_report_type_enum_values(self) -> None:
        assert ReportType.UNKNOWN.value == "unknown"
        assert ReportType.EARTHQUAKE.value == "earthquake"
        assert ReportType.TSUNAMI.value == "tsunami"
        assert ReportType.WEATHER_WARNING.value == "weather_warning"
        assert ReportType.SPECIAL_WARNING.value == "special_warning"
        assert ReportType.TYPHOON.value == "typhoon"
        assert ReportType.VOLCANO.value == "volcano"

    def test_report_type_enum_count(self) -> None:
        assert len(ReportType) == 12

    def test_earthquake_report_with_areas(self) -> None:
        areas = [Area(name="地区A", intensity="5弱"), Area(name="地区B", intensity="4")]
        report = EarthquakeReport(
            title="テスト",
            event_id="eq1",
            report_datetime=datetime.now(),
            epicenter="テスト沖",
            magnitude=6.0,
            depth_km=30.0,
            max_intensity="5弱",
            areas=areas,
        )
        assert len(report.areas) == 2
        assert report.depth_km == 30.0

    def test_tsunami_report_with_areas(self) -> None:
        areas = [TsunamiArea(name="宮城県", first_wave_time="08:00", first_wave_height="3m")]
        report = TsunamiReport(
            title="津波情報",
            event_id="ts1",
            report_datetime=datetime.now(),
            warning_level="大津波警報",
            areas=areas,
        )
        assert len(report.areas) == 1
        assert report.areas[0].first_wave_height == "3m"

    def test_weather_warning_report_with_warnings(self) -> None:
        warnings = [
            Warning(name="暴風警報", area="東京都"),
            Warning(name="大雨警報", area="神奈川県"),
        ]
        report = WeatherWarningReport(
            title="警報",
            event_id="ww1",
            report_datetime=datetime.now(),
            warnings=warnings,
        )
        assert len(report.warnings) == 2

    def test_earthquake_report_no_magnitude(self) -> None:
        report = EarthquakeReport(
            title="テスト",
            event_id="eq2",
            report_datetime=datetime.now(),
            epicenter="テスト",
        )
        assert report.magnitude is None
        assert report.depth_km is None


# ============================================================
# Tests: Parser Extended
# ============================================================

class TestParserExtended:
    def test_parse_tsunami(self) -> None:
        report = parse(TSUNAMI_XML)
        assert isinstance(report, TsunamiReport)
        assert report.warning_level == "津波警報"
        assert len(report.areas) == 2
        assert report.areas[0].name == "宮城県"
        assert report.areas[0].first_wave_height == "3m"
        assert report.areas[0].first_wave_time != ""
        assert report.areas[1].name == "福島県"

    def test_parse_weather_warning(self) -> None:
        report = parse(WEATHER_WARNING_XML)
        assert isinstance(report, WeatherWarningReport)
        assert len(report.warnings) == 2
        assert report.warnings[0].name == "暴風警報"
        assert report.warnings[0].area == "東京都"
        assert report.warnings[1].name == "大雨注意報"

    def test_parse_special_warning(self) -> None:
        report = parse(SPECIAL_WARNING_XML)
        assert isinstance(report, WeatherWarningReport)
        assert len(report.warnings) == 1
        assert report.warnings[0].name == "大雨特別警報"
        assert report.warnings[0].area == "広島県"

    def test_parse_unknown_type(self) -> None:
        report = parse(UNKNOWN_TYPE_XML)
        assert isinstance(report, BaseReport)
        assert not isinstance(report, (EarthquakeReport, TsunamiReport, WeatherWarningReport))
        assert report.title == "テスト情報"

    def test_parse_bytes_input(self) -> None:
        xml_bytes = EARTHQUAKE_XML.encode("utf-8")
        report = parse(xml_bytes)
        assert isinstance(report, EarthquakeReport)
        assert report.epicenter == "福島県沖"

    def test_parse_with_target_datetime(self) -> None:
        report = parse(EARTHQUAKE_XML)
        assert report.target_datetime is not None
        assert report.target_datetime.year == 2026

    def test_parse_earthquake_to_json_and_dict(self) -> None:
        report = parse(EARTHQUAKE_XML)
        d = report.to_dict()
        assert d["report_type"] == "earthquake"
        assert d["epicenter"] == "福島県沖"
        assert d["magnitude"] == 4.1
        json_str = report.to_json()
        data = json.loads(json_str)
        assert data["max_intensity"] == "1"

    def test_parse_tsunami_to_dict(self) -> None:
        report = parse(TSUNAMI_XML)
        d = report.to_dict()
        assert d["report_type"] == "tsunami"
        assert d["warning_level"] == "津波警報"
        assert len(d["areas"]) == 2

    def test_parse_weather_warning_to_dict(self) -> None:
        report = parse(WEATHER_WARNING_XML)
        d = report.to_dict()
        assert d["report_type"] == "weather_warning"
        assert len(d["warnings"]) == 2

    def test_parse_intensity_xml(self) -> None:
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://xml.kishou.go.jp/jmaxml1/">
<Control>
<Title>震度速報</Title>
<DateTime>2026-06-18T22:00:00Z</DateTime>
<Status>通常</Status>
<EditorialOffice>気象庁本庁</EditorialOffice>
<PublishingOffice>気象庁</PublishingOffice>
</Control>
<Head xmlns="http://xml.kishou.go.jp/jmaxml1/informationBasis1/">
<Title>震度速報</Title>
<ReportDateTime>2026-06-19T07:00:00+09:00</ReportDateTime>
<EventID>20260619070010</EventID>
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
</Report>"""
        report = parse(xml)
        assert isinstance(report, EarthquakeReport)
        assert report.max_intensity == "5弱"
        assert len(report.areas) == 2
        assert report.epicenter == ""


# ============================================================
# Tests: GeoJSON Extended
# ============================================================

class TestGeoJSONExtended:
    def test_to_geojson_tsunami(self) -> None:
        report = parse(TSUNAMI_XML)
        geojson = to_geojson(report)
        assert geojson["type"] == "Feature"
        assert geojson["properties"]["report_type"] == "tsunami"
        assert geojson["properties"]["warning_level"] == "津波警報"
        assert len(geojson["properties"]["areas"]) == 2

    def test_to_geojson_weather_warning(self) -> None:
        report = parse(WEATHER_WARNING_XML)
        geojson = to_geojson(report)
        assert geojson["type"] == "Feature"
        assert geojson["properties"]["report_type"] == "weather_warning"
        assert len(geojson["properties"]["warnings"]) == 2
        assert geojson["properties"]["warnings"][0]["name"] == "暴風警報"

    def test_to_geojson_unknown_type(self) -> None:
        report = parse(UNKNOWN_TYPE_XML)
        geojson = to_geojson(report)
        assert geojson["type"] == "Feature"
        assert geojson["properties"]["report_type"] == "unknown"
        assert geojson["geometry"] is None

    def test_to_geojson_earthquake_with_prefecture_coords(self) -> None:
        report = EarthquakeReport(
            title="東京都の地震",
            event_id="eq_coord",
            report_datetime=datetime.now(),
            epicenter="東京都",
            magnitude=4.0,
            max_intensity="3",
        )
        geojson = to_geojson(report)
        coords = geojson["geometry"]["coordinates"]
        assert coords[0] == 139.69
        assert coords[1] == 35.68

    def test_to_geojson_earthquake_epicenter_fallback(self) -> None:
        report = EarthquakeReport(
            title="福島県沖の地震",
            event_id="eq_fb",
            report_datetime=datetime.now(),
            epicenter="福島県沖",
            magnitude=5.0,
        )
        geojson = to_geojson(report)
        coords = geojson["geometry"]["coordinates"]
        assert coords != [0, 0]

    def test_to_geojson_earthquake_no_coords(self) -> None:
        report = EarthquakeReport(
            title="不明な地震",
            event_id="eq_no",
            report_datetime=datetime.now(),
            epicenter="不明な地点",
            magnitude=3.0,
        )
        geojson = to_geojson(report)
        assert geojson["geometry"] is None

    def test_to_geojson_collection_empty(self) -> None:
        geojson = to_geojson_collection([])
        assert geojson["type"] == "FeatureCollection"
        assert geojson["features"] == []

    def test_to_geojson_collection_multiple(self) -> None:
        r1 = parse(EARTHQUAKE_XML)
        r2 = parse(TSUNAMI_XML)
        geojson = to_geojson_collection([r1, r2])
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 2

    def test_get_coords_known_prefecture(self) -> None:
        coords = _get_coords("東京都")
        assert coords == (35.68, 139.69)

    def test_get_coords_partial_match(self) -> None:
        coords = _get_coords("福島県中通り")
        assert coords == (37.75, 140.47)

    def test_get_coords_unknown(self) -> None:
        coords = _get_coords("架空の県")
        assert coords is None

    def test_to_geojson_properties_common_fields(self) -> None:
        report = parse(EARTHQUAKE_XML)
        geojson = to_geojson(report)
        props = geojson["properties"]
        assert "title" in props
        assert "event_id" in props
        assert "report_type" in props
        assert "report_datetime" in props
        assert props["title"] == "震源・震度に関する情報"

    def test_to_geojson_earthquake_areas_list(self) -> None:
        report = parse(EARTHQUAKE_XML)
        geojson = to_geojson(report)
        areas = geojson["properties"]["areas"]
        assert len(areas) == 2
        assert areas[0]["name"] == "福島県中通り"
        assert areas[0]["intensity"] == "1"

    def test_to_geojson_tsunami_areas_list(self) -> None:
        report = parse(TSUNAMI_XML)
        geojson = to_geojson(report)
        areas = geojson["properties"]["areas"]
        assert len(areas) == 2
        assert "first_wave_time" in areas[0]
        assert "first_wave_height" in areas[0]
        assert "category" in areas[0]


# ============================================================
# Tests: Pandas Extended
# ============================================================

class TestPandasExtended:
    def test_to_dataframe_tsunami(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not installed")

        report = parse(TSUNAMI_XML)
        df = to_dataframe(report)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "area_name" in df.columns
        assert "first_wave_height" in df.columns
        assert df.iloc[0]["area_name"] == "宮城県"

    def test_to_dataframe_weather_warning(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not installed")

        report = parse(WEATHER_WARNING_XML)
        df = to_dataframe(report)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "warning_name" in df.columns
        assert "warning_area" in df.columns
        assert df.iloc[0]["warning_name"] == "暴風警報"

    def test_to_dataframe_unknown_type(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not installed")

        report = parse(UNKNOWN_TYPE_XML)
        df = to_dataframe(report)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    def test_to_dataframe_earthquake_expanded(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not installed")

        report = parse(EARTHQUAKE_XML)
        df = to_dataframe(report)
        assert len(df) == 2
        assert "area_name" in df.columns
        assert "area_intensity" in df.columns
        assert "epicenter" in df.columns

    def test_reports_to_dataframe_empty(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not installed")

        df = reports_to_dataframe([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_reports_to_dataframe_mixed(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not installed")

        eq = parse(EARTHQUAKE_XML)
        ts = parse(TSUNAMI_XML)
        df = reports_to_dataframe([eq, ts])
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 3

    def test_to_dataframe_custom_report(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not installed")

        report = EarthquakeReport(
            title="テスト地震",
            event_id="eq_custom",
            report_datetime=datetime.now(),
            epicenter="テスト沖",
            magnitude=5.5,
            depth_km=20.0,
            max_intensity="4",
            areas=[Area(name="テスト県", intensity="4")],
        )
        df = to_dataframe(report)
        assert len(df) == 1
        assert df.iloc[0]["magnitude"] == 5.5
        assert df.iloc[0]["depth_km"] == 20.0


# ============================================================
# Tests: Notify Extended
# ============================================================

class TestNotifyExtended:
    def test_check_report_unknown_type(self) -> None:
        report = BaseReport(
            title="テスト",
            event_id="unknown",
            report_datetime=datetime.now(),
        )
        assert check_report(report) is False

    def test_check_report_earthquake_intensity_1(self) -> None:
        report = EarthquakeReport(
            title="テスト", event_id="e1", report_datetime=datetime.now(),
            epicenter="テスト", magnitude=3.0, max_intensity="1",
        )
        assert check_report(report) is False

    def test_check_report_earthquake_intensity_2(self) -> None:
        report = EarthquakeReport(
            title="テスト", event_id="e1", report_datetime=datetime.now(),
            epicenter="テスト", magnitude=3.5, max_intensity="2",
        )
        assert check_report(report) is False

    def test_check_report_earthquake_intensity_3(self) -> None:
        report = EarthquakeReport(
            title="テスト", event_id="e1", report_datetime=datetime.now(),
            epicenter="テスト", magnitude=4.0, max_intensity="3",
        )
        assert check_report(report) is True

    def test_check_report_earthquake_intensity_4(self) -> None:
        report = EarthquakeReport(
            title="テスト", event_id="e1", report_datetime=datetime.now(),
            epicenter="テスト", magnitude=4.5, max_intensity="4",
        )
        assert check_report(report) is True

    def test_check_report_earthquake_intensity_5weak(self) -> None:
        report = EarthquakeReport(
            title="テスト", event_id="e1", report_datetime=datetime.now(),
            epicenter="テスト", magnitude=5.0, max_intensity="5弱",
        )
        assert check_report(report) is True

    def test_check_report_earthquake_intensity_5strong(self) -> None:
        report = EarthquakeReport(
            title="テスト", event_id="e1", report_datetime=datetime.now(),
            epicenter="テスト", magnitude=5.5, max_intensity="5強",
        )
        assert check_report(report) is True

    def test_check_report_earthquake_intensity_6weak(self) -> None:
        report = EarthquakeReport(
            title="テスト", event_id="e1", report_datetime=datetime.now(),
            epicenter="テスト", magnitude=6.0, max_intensity="6弱",
        )
        assert check_report(report) is True

    def test_check_report_earthquake_intensity_6strong(self) -> None:
        report = EarthquakeReport(
            title="テスト", event_id="e1", report_datetime=datetime.now(),
            epicenter="テスト", magnitude=6.5, max_intensity="6強",
        )
        assert check_report(report) is True

    def test_check_report_earthquake_intensity_7(self) -> None:
        report = EarthquakeReport(
            title="テスト", event_id="e1", report_datetime=datetime.now(),
            epicenter="テスト", magnitude=7.0, max_intensity="7",
        )
        assert check_report(report) is True

    def test_check_report_earthquake_empty_intensity(self) -> None:
        report = EarthquakeReport(
            title="テスト", event_id="e1", report_datetime=datetime.now(),
            epicenter="テスト", max_intensity="",
        )
        assert check_report(report) is False

    def test_check_report_tsunami_dai(self) -> None:
        report = TsunamiReport(
            title="テスト", event_id="t1", report_datetime=datetime.now(),
            warning_level="大津波警報",
        )
        assert check_report(report) is True

    def test_check_report_tsunami_normal(self) -> None:
        report = TsunamiReport(
            title="テスト", event_id="t1", report_datetime=datetime.now(),
            warning_level="津波警報",
        )
        assert check_report(report) is True

    def test_check_report_tsunami_chuui(self) -> None:
        report = TsunamiReport(
            title="テスト", event_id="t1", report_datetime=datetime.now(),
            warning_level="津波注意報",
        )
        assert check_report(report) is True

    def test_check_report_tsunami_unknown_level(self) -> None:
        report = TsunamiReport(
            title="テスト", event_id="t1", report_datetime=datetime.now(),
            warning_level="テスト",
        )
        assert check_report(report) is False

    def test_check_report_weather_special(self) -> None:
        report = WeatherWarningReport(
            title="テスト", event_id="w1", report_datetime=datetime.now(),
            warnings=[Warning(name="特別警報", area="東京都")],
        )
        assert check_report(report) is True

    def test_check_report_weather_storm(self) -> None:
        report = WeatherWarningReport(
            title="テスト", event_id="w1", report_datetime=datetime.now(),
            warnings=[Warning(name="暴風警報", area="東京都")],
        )
        assert check_report(report) is True

    def test_check_report_weather_heavy_rain(self) -> None:
        report = WeatherWarningReport(
            title="テスト", event_id="w1", report_datetime=datetime.now(),
            warnings=[Warning(name="大雨警報", area="東京都")],
        )
        assert check_report(report) is True

    def test_check_report_weather_snow_storm(self) -> None:
        report = WeatherWarningReport(
            title="テスト", event_id="w1", report_datetime=datetime.now(),
            warnings=[Warning(name="暴風雪警報", area="北海道")],
        )
        assert check_report(report) is True

    def test_check_report_weather_heavy_snow(self) -> None:
        report = WeatherWarningReport(
            title="テスト", event_id="w1", report_datetime=datetime.now(),
            warnings=[Warning(name="大雪警報", area="北海道")],
        )
        assert check_report(report) is True

    def test_check_report_weather_no_match(self) -> None:
        report = WeatherWarningReport(
            title="テスト", event_id="w1", report_datetime=datetime.now(),
            warnings=[Warning(name="雷注意報", area="東京都")],
        )
        assert check_report(report) is False

    def test_check_report_weather_empty_warnings(self) -> None:
        report = WeatherWarningReport(
            title="テスト", event_id="w1", report_datetime=datetime.now(),
            warnings=[],
        )
        assert check_report(report) is False

    def test_build_title_earthquake(self) -> None:
        report = EarthquakeReport(
            title="テスト", event_id="e1", report_datetime=datetime.now(),
            epicenter="テスト", max_intensity="5弱",
        )
        assert _build_title(report) == "地震情報 - 5弱"

    def test_build_title_tsunami(self) -> None:
        report = TsunamiReport(
            title="テスト", event_id="t1", report_datetime=datetime.now(),
            warning_level="津波警報",
        )
        assert _build_title(report) == "津波情報 - 津波警報"

    def test_build_title_weather_warning(self) -> None:
        report = WeatherWarningReport(
            title="テスト", event_id="w1", report_datetime=datetime.now(),
            warnings=[],
        )
        assert _build_title(report) == "気象警報"

    def test_build_title_unknown(self) -> None:
        report = BaseReport(
            title="テストタイトル", event_id="u1", report_datetime=datetime.now(),
        )
        assert _build_title(report) == "テストタイトル"

    def test_build_body_earthquake_full(self) -> None:
        report = EarthquakeReport(
            title="テスト", event_id="e1", report_datetime=datetime.now(),
            epicenter="福島県沖", magnitude=6.0, max_intensity="5強",
        )
        body = _build_body(report)
        assert "震源: 福島県沖" in body
        assert "M6.0" in body
        assert "最大震度: 5強" in body

    def test_build_body_earthquake_minimal(self) -> None:
        report = EarthquakeReport(
            title="テスト", event_id="e1", report_datetime=datetime.now(),
        )
        body = _build_body(report)
        assert body == ""

    def test_build_body_tsunami_with_areas(self) -> None:
        report = TsunamiReport(
            title="テスト", event_id="t1", report_datetime=datetime.now(),
            warning_level="津波警報",
            areas=[TsunamiArea(name="宮城県", first_wave_height="3m")],
        )
        body = _build_body(report)
        assert "警報レベル: 津波警報" in body
        assert "宮城県" in body

    def test_build_body_tsunami_no_areas(self) -> None:
        report = TsunamiReport(
            title="テスト", event_id="t1", report_datetime=datetime.now(),
            warning_level="津波警報",
        )
        body = _build_body(report)
        assert "警報レベル: 津波警報" in body

    def test_build_body_weather_warning(self) -> None:
        report = WeatherWarningReport(
            title="テスト", event_id="w1", report_datetime=datetime.now(),
            warnings=[Warning(name="暴風警報", area="東京都")],
        )
        body = _build_body(report)
        assert "暴風警報" in body

    def test_build_body_weather_warning_empty(self) -> None:
        report = WeatherWarningReport(
            title="テストタイトル", event_id="w1", report_datetime=datetime.now(),
            warnings=[],
        )
        body = _build_body(report)
        assert body == "テストタイトル"

    def test_build_body_unknown_type(self) -> None:
        report = BaseReport(
            title="テスト", event_id="u1", report_datetime=datetime.now(),
        )
        assert _build_body(report) == "テスト"

    def test_notify_non_win32(self) -> None:
        report = parse(EARTHQUAKE_XML)
        with patch.object(sys, "platform", "linux"):
            result = notify(report)
            assert result is False

    def test_notify_custom_title(self) -> None:
        report = parse(EARTHQUAKE_XML)
        with patch.object(sys, "platform", "win32"):
            with patch("jmaxml.notify._send_windows_notification", return_value=True) as mock:
                result = notify(report, title="カスタム通知")
                assert result is True
                mock.assert_called_once()
                assert mock.call_args[0][0] == "カスタム通知"


# ============================================================
# Tests: Storage Extended
# ============================================================

class TestStorageExtended:
    def test_list_all(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        r1 = parse(EARTHQUAKE_XML)
        r2 = parse(TSUNAMI_XML)
        storage.save(r1)
        storage.save(r2)
        all_reports = storage.list_all()
        assert len(all_reports) == 2

    def test_list_all_empty(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        assert storage.list_all() == []

    def test_search_by_start_date(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        report = parse(EARTHQUAKE_XML)
        storage.save(report)
        start = datetime(2026, 6, 19, 7, 35, 0)
        results = storage.search(start_date=start)
        assert len(results) == 1

    def test_search_by_end_date(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        report = parse(EARTHQUAKE_XML)
        storage.save(report)
        end = datetime(2026, 6, 19, 7, 37, 0)
        results = storage.search(end_date=end)
        assert len(results) == 1

    def test_search_by_date_range(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        report = parse(EARTHQUAKE_XML)
        storage.save(report)
        start = datetime(2026, 6, 19, 7, 0, 0)
        end = datetime(2026, 6, 19, 8, 0, 0)
        results = storage.search(start_date=start, end_date=end)
        assert len(results) == 1

    def test_search_by_report_type(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        storage.save(parse(EARTHQUAKE_XML))
        storage.save(parse(TSUNAMI_XML))
        results = storage.search(report_type="earthquake")
        assert len(results) == 1
        assert results[0].report_type == ReportType.EARTHQUAKE

    def test_search_by_date_and_type(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        storage.save(parse(EARTHQUAKE_XML))
        storage.save(parse(TSUNAMI_XML))
        start = datetime(2026, 6, 19, 0, 0, 0)
        end = datetime(2026, 6, 19, 23, 59, 59)
        results = storage.search(start_date=start, end_date=end, report_type="tsunami")
        assert len(results) == 1
        assert results[0].report_type == ReportType.TSUNAMI

    def test_search_no_results(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        storage.save(parse(EARTHQUAKE_XML))
        start = datetime(2027, 1, 1)
        results = storage.search(start_date=start)
        assert len(results) == 0

    def test_get_nonexistent(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        result = storage.get("nonexistent_id")
        assert result is None

    def test_get_tsunami_report(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        report = parse(TSUNAMI_XML)
        storage.save(report)
        retrieved = storage.get(report.event_id)
        assert isinstance(retrieved, TsunamiReport)
        assert retrieved.warning_level == "津波警報"
        assert len(retrieved.areas) == 2

    def test_get_weather_warning_report(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        report = parse(WEATHER_WARNING_XML)
        storage.save(report)
        retrieved = storage.get(report.event_id)
        assert isinstance(retrieved, WeatherWarningReport)
        assert len(retrieved.warnings) == 2

    def test_get_base_report_unknown(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        report = parse(UNKNOWN_TYPE_XML)
        storage.save(report)
        retrieved = storage.get(report.event_id)
        assert isinstance(retrieved, BaseReport)
        assert not isinstance(retrieved, (EarthquakeReport, TsunamiReport, WeatherWarningReport))

    def test_get_earthquake_report_full(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        report = parse(EARTHQUAKE_XML)
        storage.save(report)
        retrieved = storage.get(report.event_id)
        assert isinstance(retrieved, EarthquakeReport)
        assert retrieved.epicenter == "福島県沖"
        assert retrieved.magnitude == 4.1
        assert retrieved.max_intensity == "1"
        assert len(retrieved.areas) == 2

    def test_save_replace(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        r1 = EarthquakeReport(
            title="v1", event_id="same_id", report_datetime=datetime.now(),
            epicenter="テスト", max_intensity="3",
        )
        storage.save(r1)
        r2 = EarthquakeReport(
            title="v2", event_id="same_id", report_datetime=datetime.now(),
            epicenter="テスト2", max_intensity="4",
        )
        storage.save(r2)
        retrieved = storage.get("same_id")
        assert retrieved.title == "v2"
        assert storage.count() == 1

    def test_delete_nonexistent(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        assert storage.delete("nonexistent") is False

    def test_search_ordering(self, tmp_path) -> None:
        storage = SqliteStorage(str(tmp_path / "test.db"))
        r1 = EarthquakeReport(
            title="1", event_id="id1",
            report_datetime=datetime(2026, 6, 19, 7, 0),
        )
        r2 = EarthquakeReport(
            title="2", event_id="id2",
            report_datetime=datetime(2026, 6, 19, 8, 0),
        )
        storage.save(r1)
        storage.save(r2)
        results = storage.search()
        assert results[0].title == "2"
        assert results[1].title == "1"


# ============================================================
# Tests: Feed Extended
# ============================================================

class TestFeedExtended:
    def test_fetch_feed_invalid_type(self) -> None:
        client = FeedClient()
        with pytest.raises(ValueError, match="Unknown feed type"):
            client.fetch_feed("invalid_type")

    def test_feed_entry_repr(self) -> None:
        entry = FeedEntry(title="テスト", link="http://example.com", updated="2026-01-01", content="")
        assert "テスト" in repr(entry)
        assert "FeedEntry" in repr(entry)

    def test_feed_urls_keys(self) -> None:
        from jmaxml.feed import FEED_URLS
        assert "earthquake" in FEED_URLS
        assert "weather" in FEED_URLS
        assert "regular" in FEED_URLS
        assert "other" in FEED_URLS
        assert "all" in FEED_URLS
        assert len(FEED_URLS) == 5

    def test_feed_client_custom_user_agent(self) -> None:
        client = FeedClient(user_agent="test-agent/1.0")
        assert client.user_agent == "test-agent/1.0"

    def test_feed_client_default_user_agent(self) -> None:
        client = FeedClient()
        assert client.user_agent == "jmaxml-sdk/1.0"


# ============================================================
# Tests: Watcher Extended
# ============================================================

class TestWatcherExtended:
    def test_watcher_init_defaults(self) -> None:
        watcher = Watcher()
        assert watcher.feed_type == "earthquake"
        assert watcher.interval == 60
        assert watcher._seen_ids == set()

    def test_watcher_init_custom(self) -> None:
        watcher = Watcher(feed_type="weather", interval=30)
        assert watcher.feed_type == "weather"
        assert watcher.interval == 30

    def test_async_watcher_init_defaults(self) -> None:
        watcher = AsyncWatcher()
        assert watcher.feed_type == "earthquake"
        assert watcher.interval == 60
        assert watcher._seen_ids == set()

    def test_async_watcher_init_custom(self) -> None:
        watcher = AsyncWatcher(feed_type="regular", interval=120)
        assert watcher.feed_type == "regular"
        assert watcher.interval == 120


# ============================================================
# Tests: Client Extended
# ============================================================

class TestClientExtended:
    def test_client_custom_user_agent(self) -> None:
        client = Client(user_agent="custom-agent/2.0")
        assert client.feed_client.user_agent == "custom-agent/2.0"

    def test_client_default_user_agent(self) -> None:
        client = Client()
        assert client.feed_client.user_agent == "jmaxml-sdk/1.0"

    def test_client_storage_initially_none(self) -> None:
        client = Client()
        assert client._storage is None

    def test_client_enable_storage(self, tmp_path) -> None:
        client = Client()
        client.enable_storage(str(tmp_path / "test.db"))
        assert client._storage is not None

    def test_client_search_without_storage(self) -> None:
        client = Client()
        with pytest.raises(RuntimeError, match="Storage not enabled"):
            client.search()

    def test_client_search_with_storage(self, tmp_path) -> None:
        client = Client()
        client.enable_storage(str(tmp_path / "test.db"))
        report = parse(EARTHQUAKE_XML)
        client._storage.save(report)
        results = client.search()
        assert len(results) == 1

    def test_client_search_with_filters(self, tmp_path) -> None:
        client = Client()
        client.enable_storage(str(tmp_path / "test.db"))
        client._storage.save(parse(EARTHQUAKE_XML))
        client._storage.save(parse(TSUNAMI_XML))
        start = datetime(2026, 6, 19, 0, 0, 0)
        end = datetime(2026, 6, 19, 23, 59, 59)
        results = client.search(start_date=start, end_date=end, report_type="earthquake")
        assert len(results) == 1

    def test_client_get_event_with_storage(self, tmp_path) -> None:
        client = Client()
        client.enable_storage(str(tmp_path / "test.db"))
        report = parse(EARTHQUAKE_XML)
        client._storage.save(report)
        result = client.get_event(report.event_id)
        assert result is not None
        assert result.event_id == report.event_id

    def test_client_get_event_nonexistent_with_storage(self, tmp_path) -> None:
        client = Client()
        client.enable_storage(str(tmp_path / "test.db"))
        result = client.get_event("nonexistent")
        assert result is None


# ============================================================
# Tests: FastAPI Extended
# ============================================================

class TestFastAPIExtended:
    def test_create_app_with_db(self, tmp_path) -> None:
        try:
            from jmaxml.fastapi_app import create_app
        except ImportError:
            pytest.skip("fastapi not installed")

        db_path = str(tmp_path / "api_test.db")
        app = create_app(db_path=db_path)
        assert app is not None

    def test_app_root_endpoint(self) -> None:
        try:
            from jmaxml.fastapi_app import create_app
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi not installed")

        app = create_app()
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data

    def test_app_feed_endpoint(self) -> None:
        try:
            from jmaxml.fastapi_app import create_app
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi not installed")

        app = create_app()
        client = TestClient(app)
        response = client.get("/api/feed?feed_type=earthquake")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "count" in data

    def test_app_latest_endpoint(self) -> None:
        try:
            from jmaxml.fastapi_app import create_app
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi not installed")

        app = create_app()
        client = TestClient(app)
        response = client.get("/api/reports/latest?feed_type=earthquake&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        assert "count" in data

    def test_app_recent_endpoint(self) -> None:
        try:
            from jmaxml.fastapi_app import create_app
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi not installed")

        app = create_app()
        client = TestClient(app)
        response = client.get("/api/reports/recent?hours=24")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data

    def test_app_report_not_found(self) -> None:
        try:
            from jmaxml.fastapi_app import create_app
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi not installed")

        app = create_app()
        client = TestClient(app)
        response = client.get("/api/reports/nonexistent_id")
        assert response.status_code == 404

    def test_app_search_no_storage(self) -> None:
        try:
            from jmaxml.fastapi_app import create_app
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi not installed")

        app = create_app()
        client = TestClient(app)
        response = client.get("/api/reports?start_date=2026-01-01T00:00:00")
        assert response.status_code == 400

    def test_app_search_with_storage(self, tmp_path) -> None:
        try:
            from jmaxml.fastapi_app import create_app
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi not installed")

        db_path = str(tmp_path / "api_search.db")
        app = create_app(db_path=db_path)
        client = TestClient(app)
        response = client.get("/api/reports?start_date=2026-01-01T00:00:00&end_date=2026-12-31T23:59:59")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data

    def test_app_report_type_property(self) -> None:
        try:
            from jmaxml.fastapi_app import create_app
        except ImportError:
            pytest.skip("fastapi not installed")

        app = create_app()
        assert app.title == "JMAXML API"
        assert app.version == "1.0.0"


# ============================================================
# Tests: CLI Extended
# ============================================================

class TestCLIExtended:
    def test_main_no_command(self) -> None:
        from jmaxml.cli.main import main
        with patch("sys.argv", ["jmaxml"]):
            with pytest.raises(SystemExit):
                main()

    def test_main_latest_json(self) -> None:
        from jmaxml.cli.main import main
        with patch("sys.argv", ["jmaxml", "latest", "--type", "earthquake", "--json", "--limit", "1"]):
            with patch("jmaxml.Client") as MockClient:
                mock_instance = MagicMock()
                report = parse(EARTHQUAKE_XML)
                mock_instance.fetch_latest.return_value = [report]
                MockClient.return_value = mock_instance
                main()
                mock_instance.fetch_latest.assert_called_once_with("earthquake")

    def test_main_earthquake(self) -> None:
        from jmaxml.cli.main import main
        with patch("sys.argv", ["jmaxml", "earthquake", "--limit", "2"]):
            with patch("jmaxml.Client") as MockClient:
                mock_instance = MagicMock()
                report = parse(EARTHQUAKE_XML)
                mock_instance.fetch_latest.return_value = [report]
                MockClient.return_value = mock_instance
                main()
                mock_instance.fetch_latest.assert_called_once_with("earthquake")

    def test_print_reports_json(self) -> None:
        from jmaxml.cli.main import _print_reports
        report = parse(EARTHQUAKE_XML)
        _print_reports([report], as_json=True)

    def test_print_reports_text(self) -> None:
        from jmaxml.cli.main import _print_reports
        report = parse(EARTHQUAKE_XML)
        _print_reports([report], as_json=False)

    def test_print_report_json(self) -> None:
        from jmaxml.cli.main import _print_report
        report = parse(EARTHQUAKE_XML)
        _print_report(report, as_json=True)

    def test_print_report_text(self) -> None:
        from jmaxml.cli.main import _print_report
        report = parse(EARTHQUAKE_XML)
        _print_report(report, as_json=False)

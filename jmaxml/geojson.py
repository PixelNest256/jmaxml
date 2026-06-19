"""JMAXML GeoJSON output - convert reports to GeoJSON format."""

from __future__ import annotations

from typing import Any

from jmaxml.models import (
    BaseReport,
    EarthquakeReport,
    TsunamiReport,
    WeatherWarningReport,
)


# Prefecture approximate coordinates (lat, lon)
PREFECTURE_COORDS: dict[str, tuple[float, float]] = {
    "北海道": (43.06, 141.35),
    "青森県": (40.82, 140.74),
    "岩手県": (39.70, 141.15),
    "宮城県": (38.27, 140.87),
    "秋田県": (39.72, 140.10),
    "山形県": (38.24, 140.34),
    "福島県": (37.75, 140.47),
    "茨城県": (36.34, 140.45),
    "栃木県": (36.57, 139.88),
    "群馬県": (36.39, 139.06),
    "埼玉県": (35.86, 139.65),
    "千葉県": (35.61, 140.12),
    "東京都": (35.68, 139.69),
    "神奈川県": (35.45, 139.64),
    "新潟県": (37.90, 139.02),
    "富山県": (36.70, 137.21),
    "石川県": (36.59, 136.63),
    "福井県": (36.07, 136.22),
    "山梨県": (35.66, 138.57),
    "長野県": (36.23, 138.18),
    "岐阜県": (35.39, 136.72),
    "静岡県": (34.98, 138.38),
    "愛知県": (35.18, 136.91),
    "三重県": (34.73, 136.51),
    "滋賀県": (35.00, 135.87),
    "京都府": (35.02, 135.77),
    "大阪府": (34.69, 135.52),
    "兵庫県": (34.69, 135.18),
    "奈良県": (34.69, 135.83),
    "和歌山県": (34.23, 135.17),
    "鳥取県": (35.50, 134.24),
    "島根県": (35.47, 133.05),
    "岡山県": (34.66, 133.93),
    "広島県": (34.40, 132.46),
    "山口県": (34.19, 131.47),
    "徳島県": (34.07, 134.56),
    "香川県": (34.34, 134.04),
    "愛媛県": (33.84, 132.77),
    "高知県": (33.56, 133.53),
    "福岡県": (33.61, 130.42),
    "佐賀県": (33.25, 130.30),
    "長崎県": (32.74, 129.87),
    "熊本県": (32.79, 130.74),
    "大分県": (33.24, 131.61),
    "宮崎県": (31.91, 131.42),
    "鹿児島県": (31.56, 130.56),
    "沖縄県": (26.34, 127.68),
}


def _get_coords(area_name: str) -> tuple[float, float] | None:
    for pref, coords in PREFECTURE_COORDS.items():
        if pref in area_name:
            return coords
    return None


def to_geojson(report: BaseReport) -> dict[str, Any]:
    """Convert a report to GeoJSON Feature.

    Usage:
        from jmaxml import parse
        from jmaxml.geojson import to_geojson

        report = parse(xml_text)
        geojson = to_geojson(report)
    """
    properties: dict[str, Any] = {
        "title": report.title,
        "event_id": report.event_id,
        "report_type": report.report_type.value,
        "report_datetime": report.report_datetime.isoformat(),
    }

    if isinstance(report, EarthquakeReport):
        properties["epicenter"] = report.epicenter
        properties["magnitude"] = report.magnitude
        properties["depth_km"] = report.depth_km
        properties["max_intensity"] = report.max_intensity
        if report.areas:
            properties["areas"] = [
                {"name": a.name, "intensity": a.intensity}
                for a in report.areas
            ]

    if isinstance(report, TsunamiReport):
        properties["warning_level"] = report.warning_level
        if report.areas:
            properties["areas"] = [
                {
                    "name": a.name,
                    "first_wave_time": a.first_wave_time,
                    "first_wave_height": a.first_wave_height,
                    "category": a.category,
                }
                for a in report.areas
            ]

    if isinstance(report, WeatherWarningReport):
        if report.warnings:
            properties["warnings"] = [
                {"name": w.name, "area": w.area}
                for w in report.warnings
            ]

    coords: tuple[float, float] | None = None
    if isinstance(report, EarthquakeReport) and report.epicenter:
        coords = _get_coords(report.epicenter)
    if coords is None and report.title:
        for pref, c in PREFECTURE_COORDS.items():
            if pref in report.title:
                coords = c
                break

    geometry: dict[str, Any]
    if coords is not None:
        geometry = {
            "type": "Point",
            "coordinates": [coords[1], coords[0]],
        }
    else:
        geometry = None

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": properties,
    }


def to_geojson_collection(reports: list[BaseReport]) -> dict[str, Any]:
    """Convert multiple reports to a GeoJSON FeatureCollection.

    Usage:
        from jmaxml import Client
        from jmaxml.geojson import to_geojson_collection

        client = Client()
        reports = client.fetch_recent()
        geojson = to_geojson_collection(reports)
    """
    features = [to_geojson(r) for r in reports]
    return {
        "type": "FeatureCollection",
        "features": features,
    }

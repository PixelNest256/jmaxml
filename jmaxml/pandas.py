"""JMAXML Pandas integration - DataFrame conversion for reports."""

from __future__ import annotations

from typing import Any

from jmaxml.models import (
    BaseReport,
    EarthquakeReport,
    TsunamiReport,
    WeatherWarningReport,
)


def to_dataframe(report: BaseReport) -> Any:
    """Convert a report to a pandas DataFrame.

    Usage:
        from jmaxml import parse
        from jmaxml.pandas import to_dataframe

        report = parse(xml_text)
        df = to_dataframe(report)
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("pandas is required. Install with: pip install pandas") from e

    data = report.to_dict()

    if isinstance(report, EarthquakeReport) and report.areas:
        rows = []
        for area in report.areas:
            row = {
                "title": report.title,
                "event_id": report.event_id,
                "report_datetime": report.report_datetime,
                "report_type": report.report_type.value,
                "epicenter": report.epicenter,
                "magnitude": report.magnitude,
                "depth_km": report.depth_km,
                "max_intensity": report.max_intensity,
                "area_name": area.name,
                "area_intensity": area.intensity,
            }
            rows.append(row)
        return pd.DataFrame(rows)

    if isinstance(report, TsunamiReport) and report.areas:
        rows = []
        for area in report.areas:
            row = {
                "title": report.title,
                "event_id": report.event_id,
                "report_datetime": report.report_datetime,
                "report_type": report.report_type.value,
                "warning_level": report.warning_level,
                "area_name": area.name,
                "first_wave_time": area.first_wave_time,
                "first_wave_height": area.first_wave_height,
                "category": area.category,
            }
            rows.append(row)
        return pd.DataFrame(rows)

    if isinstance(report, WeatherWarningReport) and report.warnings:
        rows = []
        for warning in report.warnings:
            row = {
                "title": report.title,
                "event_id": report.event_id,
                "report_datetime": report.report_datetime,
                "report_type": report.report_type.value,
                "warning_name": warning.name,
                "warning_area": warning.area,
            }
            rows.append(row)
        return pd.DataFrame(rows)

    return pd.DataFrame([data])


def reports_to_dataframe(reports: list[BaseReport]) -> Any:
    """Convert multiple reports to a pandas DataFrame.

    Usage:
        from jmaxml import Client
        from jmaxml.pandas import reports_to_dataframe

        client = Client()
        reports = client.fetch_recent()
        df = reports_to_dataframe(reports)
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("pandas is required. Install with: pip install pandas") from e

    dfs = [to_dataframe(r) for r in reports]
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

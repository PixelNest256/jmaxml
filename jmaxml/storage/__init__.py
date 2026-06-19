"""JMAXML Storage - SQLite persistence for reports."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from typing import Any

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

logger = logging.getLogger(__name__)


class SqliteStorage:
    """Store reports in SQLite database.

    Usage:
        storage = SqliteStorage("reports.db")
        storage.save(report)
        reports = storage.search(start_date=...)
    """

    def __init__(self, db_path: str = "jmaxml_reports.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    event_id TEXT PRIMARY KEY,
                    title TEXT,
                    report_type TEXT,
                    report_datetime TEXT,
                    target_datetime TEXT,
                    json_data TEXT
                )
            """)
            conn.commit()

    def save(self, report: BaseReport) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO reports
                   (event_id, title, report_type, report_datetime, target_datetime, json_data)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    report.event_id,
                    report.title,
                    report.report_type.value,
                    report.report_datetime.isoformat(),
                    report.target_datetime.isoformat() if report.target_datetime else None,
                    report.to_json(),
                ),
            )
            conn.commit()

    def get(self, event_id: str) -> BaseReport | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT json_data FROM reports WHERE event_id = ?", (event_id,)
            )
            row = cursor.fetchone()
            if row:
                data = json.loads(row[0])
                return self._dict_to_report(data)
        return None

    def _dict_to_report(self, data: dict) -> BaseReport:
        report_type = ReportType(data.get("report_type", "unknown"))
        report_datetime = datetime.fromisoformat(data["report_datetime"])
        target_datetime = None
        if data.get("target_datetime"):
            target_datetime = datetime.fromisoformat(data["target_datetime"])

        if report_type == ReportType.EARTHQUAKE:
            areas = [Area(name=a["name"], intensity=a.get("intensity", "")) for a in data.get("areas", [])]
            return EarthquakeReport(
                title=data["title"],
                event_id=data["event_id"],
                report_datetime=report_datetime,
                target_datetime=target_datetime,
                epicenter=data.get("epicenter", ""),
                magnitude=data.get("magnitude"),
                depth_km=data.get("depth_km"),
                max_intensity=data.get("max_intensity", ""),
                areas=areas,
            )
        elif report_type == ReportType.TSUNAMI:
            areas = [
                TsunamiArea(
                    name=a["name"],
                    first_wave_time=a.get("first_wave_time", ""),
                    first_wave_height=a.get("first_wave_height", ""),
                    category=a.get("category", ""),
                )
                for a in data.get("areas", [])
            ]
            return TsunamiReport(
                title=data["title"],
                event_id=data["event_id"],
                report_datetime=report_datetime,
                target_datetime=target_datetime,
                warning_level=data.get("warning_level", ""),
                areas=areas,
            )
        elif report_type == ReportType.WEATHER_WARNING:
            warnings = [Warning(name=w["name"], area=w.get("area", "")) for w in data.get("warnings", [])]
            return WeatherWarningReport(
                title=data["title"],
                event_id=data["event_id"],
                report_datetime=report_datetime,
                target_datetime=target_datetime,
                warnings=warnings,
            )

        return BaseReport(
            title=data["title"],
            event_id=data["event_id"],
            report_datetime=report_datetime,
            target_datetime=target_datetime,
        )

    def search(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        report_type: str | None = None,
    ) -> list[BaseReport]:
        conditions: list[str] = []
        params: list[Any] = []

        if start_date is not None:
            if not isinstance(start_date, datetime):
                raise TypeError(f"start_date must be a datetime, got {type(start_date).__name__}")
            conditions.append("report_datetime >= ?")
            params.append(start_date.isoformat())
        if end_date is not None:
            if not isinstance(end_date, datetime):
                raise TypeError(f"end_date must be a datetime, got {type(end_date).__name__}")
            conditions.append("report_datetime <= ?")
            params.append(end_date.isoformat())
        if report_type is not None:
            if not isinstance(report_type, str):
                raise TypeError(f"report_type must be a str, got {type(report_type).__name__}")
            conditions.append("report_type = ?")
            params.append(report_type)

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"SELECT json_data FROM reports{where} ORDER BY report_datetime DESC", params)
            return [self._dict_to_report(json.loads(row[0])) for row in cursor.fetchall()]

    def list_all(self) -> list[BaseReport]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT json_data FROM reports ORDER BY report_datetime DESC")
            return [self._dict_to_report(json.loads(row[0])) for row in cursor.fetchall()]

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM reports")
            return cursor.fetchone()[0]

    def delete(self, event_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM reports WHERE event_id = ?", (event_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM reports")
            conn.commit()
            return cursor.rowcount

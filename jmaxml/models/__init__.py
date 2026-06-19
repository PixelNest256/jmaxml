"""JMAXML models - data classes for JMA XML reports."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any
import json


class ReportType(Enum):
    UNKNOWN = "unknown"
    EARTHQUAKE = "earthquake"
    TSUNAMI = "tsunami"
    WEATHER_WARNING = "weather_warning"
    SPECIAL_WARNING = "special_warning"
    TYPHOON = "typhoon"
    VOLCANO = "volcano"
    ASHFALL = "ashfall"
    WEATHER_FORECAST = "weather_forecast"
    WEATHER_INFO = "weather_info"
    MARINE_FORECAST = "marine_forecast"
    EARLY_WARNING = "early_warning"


@dataclass
class Area:
    name: str
    intensity: str = ""


@dataclass
class TsunamiArea:
    name: str
    first_wave_time: str = ""
    first_wave_height: str = ""
    category: str = ""


@dataclass
class Warning:
    name: str
    area: str = ""


@dataclass
class BaseReport:
    title: str
    event_id: str
    report_datetime: datetime
    target_datetime: datetime | None = None
    _detected_type: ReportType | None = field(default=None, repr=False)

    @property
    def report_type(self) -> ReportType:
        return self._detected_type or ReportType.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("_detected_type", None)
        d["report_type"] = self.report_type.value
        d["report_datetime"] = self.report_datetime.isoformat()
        if self.target_datetime:
            d["target_datetime"] = self.target_datetime.isoformat()
        return d

    def to_json(self, indent: int | None = None) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} title={self.title!r}>"


@dataclass
class EarthquakeReport(BaseReport):
    epicenter: str = ""
    magnitude: float | None = None
    depth_km: float | None = None
    max_intensity: str = ""
    areas: list[Area] = field(default_factory=list)

    @property
    def report_type(self) -> ReportType:
        return ReportType.EARTHQUAKE


@dataclass
class TsunamiReport(BaseReport):
    warning_level: str = ""
    areas: list[TsunamiArea] = field(default_factory=list)

    @property
    def report_type(self) -> ReportType:
        return ReportType.TSUNAMI


@dataclass
class WeatherWarningReport(BaseReport):
    warnings: list[Warning] = field(default_factory=list)

    @property
    def report_type(self) -> ReportType:
        return ReportType.WEATHER_WARNING


__all__ = [
    "ReportType",
    "BaseReport",
    "EarthquakeReport",
    "TsunamiReport",
    "TsunamiArea",
    "WeatherWarningReport",
    "Warning",
    "Area",
]

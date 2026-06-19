"""JMAXML SDK - Python SDK for Japan Meteorological Agency Disaster XML"""

from jmaxml.client import Client
from jmaxml.parser import parse
from jmaxml.feed import FeedClient, FeedEntry
from jmaxml.feed.watcher import Watcher, AsyncWatcher
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
from jmaxml.storage import SqliteStorage
from jmaxml.pandas import to_dataframe, reports_to_dataframe
from jmaxml.geojson import to_geojson, to_geojson_collection
from jmaxml.notify import notify, check_report

__version__ = "1.0.0"
__all__ = [
    "Client",
    "parse",
    "FeedClient",
    "FeedEntry",
    "Watcher",
    "AsyncWatcher",
    "Area",
    "BaseReport",
    "EarthquakeReport",
    "ReportType",
    "TsunamiArea",
    "TsunamiReport",
    "Warning",
    "WeatherWarningReport",
    "SqliteStorage",
    "to_dataframe",
    "reports_to_dataframe",
    "to_geojson",
    "to_geojson_collection",
    "notify",
    "check_report",
]

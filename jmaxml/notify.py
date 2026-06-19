"""JMAXML Windows Notification - send desktop notifications for reports."""

from __future__ import annotations

import sys
from typing import Any

from jmaxml.models import (
    BaseReport,
    EarthquakeReport,
    ReportType,
    TsunamiReport,
    WeatherWarningReport,
)


def notify(report: BaseReport, title: str | None = None, timeout: int = 10) -> bool:
    """Send a Windows desktop notification for a report.

    Usage:
        from jmaxml import parse
        from jmaxml.notify import notify

        report = parse(xml_text)
        notify(report)
    """
    if sys.platform != "win32":
        return False

    notification_title = title or _build_title(report)
    notification_body = _build_body(report)

    return _send_windows_notification(notification_title, notification_body, timeout)


def _build_title(report: BaseReport) -> str:
    if isinstance(report, EarthquakeReport):
        return f"地震情報 - {report.max_intensity}"
    elif isinstance(report, TsunamiReport):
        return f"津波情報 - {report.warning_level}"
    elif isinstance(report, WeatherWarningReport):
        return "気象警報"
    return report.title


def _build_body(report: BaseReport) -> str:
    if isinstance(report, EarthquakeReport):
        parts = []
        if report.epicenter:
            parts.append(f"震源: {report.epicenter}")
        if report.magnitude is not None:
            parts.append(f"M{report.magnitude}")
        if report.max_intensity:
            parts.append(f"最大震度: {report.max_intensity}")
        return " | ".join(parts)

    if isinstance(report, TsunamiReport):
        parts = []
        if report.warning_level:
            parts.append(f"警報レベル: {report.warning_level}")
        for area in report.areas[:3]:
            parts.append(f"{area.name}: {area.first_wave_height}")
        return " | ".join(parts)

    if isinstance(report, WeatherWarningReport):
        parts = []
        for w in report.warnings[:3]:
            parts.append(w.name)
        return ", ".join(parts) if parts else report.title

    return report.title


def _send_windows_notification(title: str, message: str, timeout: int = 10) -> bool:
    try:
        from win11toast import toast
        toast(title, message)
        return True
    except ImportError:
        pass
    except Exception:
        pass

    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            title,
            message,
            duration=timeout,
            threaded=False,
        )
        return True
    except ImportError:
        pass
    except Exception:
        pass

    return False


def check_report(report: BaseReport) -> bool:
    """Check if a report should trigger a notification."""
    if isinstance(report, EarthquakeReport):
        intensity_order = ["1", "2", "3", "4", "5弱", "5強", "6弱", "6強", "7"]
        if report.max_intensity in intensity_order:
            idx = intensity_order.index(report.max_intensity)
            return idx >= 2  # 3以上
        return False

    if isinstance(report, TsunamiReport):
        return report.warning_level in ["大津波警報", "津波警報", "津波注意報"]

    if isinstance(report, WeatherWarningReport):
        special_keywords = ["特別警報", "暴風", "大雨", "暴風雪", "大雪"]
        return any(k in w.name for w in report.warnings for k in special_keywords)

    return False

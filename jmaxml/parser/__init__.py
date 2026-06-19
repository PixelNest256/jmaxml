"""JMAXML Parser - converts JMA XML to Python objects."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Union

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

NS = {
    "jmx": "http://xml.kishou.go.jp/jmaxml1/",
    "jmx_head": "http://xml.kishou.go.jp/jmaxml1/informationBasis1/",
    "jmx_body": "http://xml.kishou.go.jp/jmaxml1/body/seismology1/",
    "jmx_eb": "http://xml.kishou.go.jp/jmaxml1/elementBasis1/",
}


def _local_name(elem: ET.Element) -> str:
    tag = elem.tag
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _find_text(root: ET.Element, *paths: str) -> str:
    for path in paths:
        elem = root.find(path, NS)
        if elem is None:
            elem = root.find(path)
        if elem is not None and elem.text:
            return elem.text.strip()
    return ""


def _detect_report_type(root: ET.Element) -> ReportType:
    title = _find_text(root, ".//jmx:Control/jmx:Title", ".//Control/Title")
    if not title:
        return ReportType.UNKNOWN

    if "震度速報" in title:
        return ReportType.EARTHQUAKE
    elif "震源" in title or "震度" in title:
        return ReportType.EARTHQUAKE
    elif "津波" in title:
        return ReportType.TSUNAMI
    elif "降灰" in title:
        return ReportType.ASHFALL
    elif "火山" in title:
        return ReportType.VOLCANO
    elif "早期注意" in title:
        return ReportType.EARLY_WARNING
    elif "海上予報" in title or "海上警報" in title:
        return ReportType.MARINE_FORECAST
    elif "天気予報" in title:
        return ReportType.WEATHER_FORECAST
    elif "天気概況" in title or "気象情報" in title or "気象解説" in title:
        return ReportType.WEATHER_INFO
    elif "特別警報" in title:
        return ReportType.SPECIAL_WARNING
    elif "警報" in title or "注意報" in title:
        return ReportType.WEATHER_WARNING
    elif "台風" in title:
        return ReportType.TYPHOON

    return ReportType.UNKNOWN


def _parse_control(root: ET.Element) -> dict:
    title = ""
    event_id = ""
    report_datetime: datetime | None = None
    target_datetime: datetime | None = None

    control = root.find("jmx:Control", NS)
    if control is None:
        control = root.find(".//Control")

    if control is not None:
        for child in control:
            ln = _local_name(child)
            if ln == "Title" and child.text:
                title = child.text.strip()
            elif ln == "DateTime" and child.text:
                try:
                    report_datetime = datetime.fromisoformat(child.text)
                except ValueError:
                    logger.debug("Invalid DateTime in Control: %s", child.text)

    head = root.find("jmx_head:Head", NS)
    if head is None:
        head = root.find(".//Head")

    if head is not None:
        for child in head:
            ln = _local_name(child)
            if ln == "EventID" and child.text:
                event_id = child.text.strip()
            elif ln == "ReportDateTime" and child.text:
                try:
                    report_datetime = datetime.fromisoformat(child.text)
                except ValueError:
                    logger.debug("Invalid ReportDateTime: %s", child.text)
            elif ln == "TargetDateTime" and child.text:
                try:
                    target_datetime = datetime.fromisoformat(child.text)
                except ValueError:
                    logger.debug("Invalid TargetDateTime: %s", child.text)

    return {
        "title": title,
        "event_id": event_id,
        "report_datetime": report_datetime,
        "target_datetime": target_datetime,
    }


def _find_body(root: ET.Element) -> ET.Element | None:
    body = root.find("jmx_body:Body", NS)
    if body is None:
        body = root.find(".//Body")
    return body


def _find_elem(parent: ET.Element, local_name: str) -> ET.Element | None:
    elem = parent.find(f"jmx_body:{local_name}", NS)
    if elem is None:
        elem = parent.find(f".//{local_name}")
    return elem


def _parse_earthquake(root: ET.Element, base_data: dict) -> EarthquakeReport:
    epicenter = ""
    magnitude: float | None = None
    depth_km: float | None = None
    max_intensity = ""
    areas: list[Area] = []

    body = _find_body(root)
    if body is not None:
        earthquake = _find_elem(body, "Earthquake")

        if earthquake is not None:
            hypocenter = _find_elem(earthquake, "Hypocenter")

            if hypocenter is not None:
                area = _find_elem(hypocenter, "Area")

                if area is not None:
                    for child in area:
                        ln = _local_name(child)
                        if ln == "Name" and child.text:
                            epicenter = child.text.strip()

            for child in earthquake:
                if _local_name(child) == "Magnitude" and child.text:
                    try:
                        magnitude = float(child.text.strip())
                    except ValueError:
                        pass
                    break

        intensity = _find_elem(body, "Intensity")

        if intensity is not None:
            observation = _find_elem(intensity, "Observation")

            if observation is not None:
                max_int = _find_text(observation, "jmx_body:MaxInt", "MaxInt")
                if max_int:
                    max_intensity = max_int

                for pref in observation.findall("jmx_body:Pref", NS):
                    for area_elem in pref.findall("jmx_body:Area", NS):
                        name = _find_text(area_elem, "jmx_body:Name", "Name")
                        area_intensity = _find_text(area_elem, "jmx_body:MaxInt", "MaxInt")
                        if name:
                            areas.append(Area(name=name, intensity=area_intensity))

    return EarthquakeReport(
        title=base_data["title"],
        event_id=base_data["event_id"],
        report_datetime=base_data["report_datetime"],
        target_datetime=base_data["target_datetime"],
        epicenter=epicenter,
        magnitude=magnitude,
        depth_km=depth_km,
        max_intensity=max_intensity,
        areas=areas,
    )


def _parse_tsunami(root: ET.Element, base_data: dict) -> TsunamiReport:
    warning_level = ""
    areas: list[TsunamiArea] = []

    body = _find_body(root)
    if body is not None:
        tsunami = _find_elem(body, "Tsunami")

        if tsunami is not None:
            for child in tsunami:
                ln = _local_name(child)
                if ln == "Category" and child.text:
                    warning_level = child.text.strip()
                elif ln == "Area":
                    name = ""
                    first_wave_time = ""
                    first_wave_height = ""
                    category = ""
                    for area_child in child:
                        aln = _local_name(area_child)
                        if aln == "Name" and area_child.text:
                            name = area_child.text.strip()
                        elif aln == "ArrivalTime" and area_child.text:
                            first_wave_time = area_child.text.strip()
                        elif aln == "Height" and area_child.text:
                            first_wave_height = area_child.text.strip()
                        elif aln == "Category" and area_child.text:
                            category = area_child.text.strip()
                    if name:
                        areas.append(TsunamiArea(
                            name=name,
                            first_wave_time=first_wave_time,
                            first_wave_height=first_wave_height,
                            category=category,
                        ))

    return TsunamiReport(
        title=base_data["title"],
        event_id=base_data["event_id"],
        report_datetime=base_data["report_datetime"],
        target_datetime=base_data["target_datetime"],
        warning_level=warning_level,
        areas=areas,
    )


def _parse_weather_warning(root: ET.Element, base_data: dict) -> WeatherWarningReport:
    warnings: list[Warning] = []

    body = _find_body(root)
    if body is not None:
        warning_elem = _find_elem(body, "Warning")

        if warning_elem is not None:
            for area in warning_elem:
                if _local_name(area) != "Area":
                    continue
                area_name = _find_text(area, "jmx_body:Name", "Name")
                for item in area:
                    if _local_name(item) != "Item":
                        continue
                    warning_name = _find_text(item, "jmx_body:Name", "Name")
                    if warning_name:
                        warnings.append(Warning(name=warning_name, area=area_name))

    return WeatherWarningReport(
        title=base_data["title"],
        event_id=base_data["event_id"],
        report_datetime=base_data["report_datetime"],
        target_datetime=base_data["target_datetime"],
        warnings=warnings,
    )


def parse(xml: str | bytes) -> BaseReport:
    root = ET.fromstring(xml)

    report_type = _detect_report_type(root)
    base_data = _parse_control(root)

    if base_data["report_datetime"] is None:
        base_data["report_datetime"] = datetime.now()
        logger.warning("report_datetime not found in XML, using current time")

    if report_type == ReportType.EARTHQUAKE:
        return _parse_earthquake(root, base_data)

    if report_type == ReportType.TSUNAMI:
        return _parse_tsunami(root, base_data)

    if report_type in (ReportType.WEATHER_WARNING, ReportType.SPECIAL_WARNING):
        return _parse_weather_warning(root, base_data)

    return BaseReport(**base_data, _detected_type=report_type)

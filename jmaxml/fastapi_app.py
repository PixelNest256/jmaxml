"""JMAXML FastAPI integration - Web API for JMA disaster reports."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from jmaxml.client import Client
from jmaxml.models import BaseReport


def create_app(db_path: str | None = None) -> Any:
    """Create a FastAPI app for serving JMA reports.

    Usage:
        from jmaxml.fastapi_app import create_app

        app = create_app()
        # uvicorn jmaxml.fastapi_app:app --reload
    """
    try:
        from fastapi import FastAPI, Query, HTTPException
    except ImportError:
        raise ImportError("fastapi is required. Install with: pip install fastapi uvicorn")

    app = FastAPI(
        title="JMAXML API",
        description="気象庁防災情報XML API",
        version="1.0.0",
    )

    client = Client()
    if db_path:
        client.enable_storage(db_path)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "JMAXML API", "docs": "/docs"}

    @app.get("/api/reports/latest")
    async def get_latest(
        feed_type: str = Query("earthquake", description="フィード種別"),
        limit: int = Query(10, ge=1, le=100, description="取得件数"),
    ) -> dict[str, Any]:
        reports = await asyncio.to_thread(client.fetch_latest, feed_type)
        return {
            "reports": [r.to_dict() for r in reports[:limit]],
            "count": len(reports[:limit]),
        }

    @app.get("/api/reports/recent")
    async def get_recent(
        hours: int = Query(24, ge=1, le=168, description="取得期間（時間）"),
        report_type: str | None = Query(None, description="電文種別"),
    ) -> dict[str, Any]:
        reports = await asyncio.to_thread(
            client.fetch_recent, hours=hours, report_type=report_type
        )
        return {
            "reports": [r.to_dict() for r in reports],
            "count": len(reports),
        }

    @app.get("/api/reports/{event_id}")
    async def get_report(event_id: str) -> dict[str, Any]:
        report = await asyncio.to_thread(client.get_event, event_id)
        if report is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Report not found")
        return report.to_dict()

    @app.get("/api/reports")
    async def search_reports(
        start_date: str | None = Query(None, description="開始日時 (ISO format)"),
        end_date: str | None = Query(None, description="終了日時 (ISO format)"),
        report_type: str | None = Query(None, description="電文種別"),
    ) -> dict[str, Any]:
        if not client._storage:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail="Storage not enabled. Start server with --db option."
            )

        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        reports = await asyncio.to_thread(
            client.search, start_date=start, end_date=end, report_type=report_type
        )
        return {
            "reports": [r.to_dict() for r in reports],
            "count": len(reports),
        }

    @app.get("/api/feed")
    async def get_feed(
        feed_type: str = Query("earthquake", description="フィード種別"),
    ) -> dict[str, Any]:
        entries = await asyncio.to_thread(client.fetch_feed, feed_type)
        return {
            "entries": [
                {
                    "title": e.title,
                    "link": e.link,
                    "updated": e.updated,
                    "content": e.content,
                }
                for e in entries
            ],
            "count": len(entries),
        }

    return app


app: Any = None


def get_app() -> Any:
    global app
    if app is None:
        app = create_app()
    return app

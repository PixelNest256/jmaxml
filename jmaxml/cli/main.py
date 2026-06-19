"""JMAXML CLI - command line interface."""

from __future__ import annotations

import argparse
import json
import sys

from jmaxml.models import ReportType

EARTHQUAKE_TYPES = {ReportType.EARTHQUAKE, ReportType.TSUNAMI}
VOLCANO_TYPES = {ReportType.VOLCANO, ReportType.ASHFALL}


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jmaxml",
        description="JMAXML SDK - 気象庁防災情報XML CLI",
    )

    subparsers = parser.add_subparsers(dest="command", help="コマンド")

    # latest
    latest_parser = subparsers.add_parser("latest", help="最新の電文を取得")
    latest_parser.add_argument("--type", default="earthquake", help="フィード種別 (earthquake/weather/regular/other/all)")
    latest_parser.add_argument("--json", action="store_true", help="JSON出力")
    latest_parser.add_argument("--limit", type=int, default=10, help="取得件数")

    # earthquake
    eq_parser = subparsers.add_parser("earthquake", help="地震情報を取得")
    eq_parser.add_argument("--json", action="store_true", help="JSON出力")
    eq_parser.add_argument("--limit", type=int, default=10, help="取得件数")

    # volcano
    vol_parser = subparsers.add_parser("volcano", help="火山情報を取得")
    vol_parser.add_argument("--json", action="store_true", help="JSON出力")
    vol_parser.add_argument("--limit", type=int, default=10, help="取得件数")

    # watch
    watch_parser = subparsers.add_parser("watch", help="新しい電文を監視")
    watch_parser.add_argument("--type", default="earthquake", help="フィード種別")
    watch_parser.add_argument("--interval", type=int, default=60, help="確認間隔（秒）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    from jmaxml import Client

    client = Client()

    if args.command == "latest":
        reports = client.fetch_latest(args.type)[:args.limit]
        _print_reports(reports, args.json)

    elif args.command == "earthquake":
        reports = client.fetch_latest("earthquake")
        reports = [r for r in reports if r.report_type in EARTHQUAKE_TYPES][:args.limit]
        _print_reports(reports, args.json)

    elif args.command == "volcano":
        reports = client.fetch_latest("earthquake")
        reports = [r for r in reports if r.report_type in VOLCANO_TYPES][:args.limit]
        _print_reports(reports, args.json)

    elif args.command == "watch":
        print(f"監視を開始しました ({args.type})... Ctrl+C で停止")
        try:
            for report in client.watch(args.type, args.interval):
                _print_report(report, False)
        except KeyboardInterrupt:
            print("\n監視を停止しました。")


def _print_reports(reports: list, as_json: bool) -> None:
    if as_json:
        data = [r.to_dict() for r in reports]
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            _print_report(report, False)


def _print_report(report, as_json: bool) -> None:
    if as_json:
        print(report.to_json(indent=2))
    else:
        print(f"[{report.report_type.value}] {report.title}")
        print(f"  EventID: {report.event_id}")
        print(f"  時刻: {report.report_datetime}")
        print()


if __name__ == "__main__":
    main()

"""地震情報モニターサンプル - 最新の地震情報を取得して表示"""

from jmaxml import Client, EarthquakeReport


def main():
    print("=" * 60)
    print("  JMAXML SDK 地震情報モニター")
    print("=" * 60)

    client = Client()

    # フィード一覧の取得
    print("\n[1] 地震フィードの取得")
    print("-" * 40)
    entries = client.fetch_feed("earthquake")
    print(f"  取得件数: {len(entries)}")
    for i, entry in enumerate(entries[:5], 1):
        print(f"  [{i}] {entry.title}")
        print(f"      更新: {entry.updated}")

    # 最新の地震情報取得
    print("\n[2] 最新の地震情報")
    print("-" * 40)
    reports = client.fetch_latest("earthquake")
    print(f"  取得件数: {len(reports)}")

    for report in reports[:3]:
        print(f"\n  --- {report.title} ---")
        print(f"  イベントID: {report.event_id}")
        print(f"  レポート時刻: {report.report_datetime}")

        if isinstance(report, EarthquakeReport):
            print(f"  震源: {report.epicenter}")
            if report.magnitude is not None:
                print(f"  マグニチュード: M{report.magnitude}")
            print(f"  最大震度: {report.max_intensity}")
            if report.areas:
                print(f"  影響エリア:")
                for area in report.areas[:5]:
                    print(f"    - {area.name}: 震度{area.intensity}")
                if len(report.areas) > 5:
                    print(f"    ... 他{len(report.areas) - 5}エリア")

    print("\n完了!")


if __name__ == "__main__":
    main()

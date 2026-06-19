"""SQLite保存サンプル - レポートをSQLiteデータベースに保存・検索"""

import os
from datetime import datetime, timedelta
from jmaxml import Client, parse, EarthquakeReport, SqliteStorage

EARTHQUAKE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://xml.kishou.go.jp/jmaxml1/">
<Control>
<Title>震源・震度に関する情報</Title>
<DateTime>2026-06-18T22:36:29Z</DateTime>
<Status>通常</Status>
<EditorialOffice>気象庁本庁</EditorialOffice>
<PublishingOffice>気象庁</PublishingOffice>
</Control>
<Head xmlns="http://xml.kishou.go.jp/jmaxml1/informationBasis1/">
<Title>震源・震度情報</Title>
<ReportDateTime>2026-06-19T07:36:00+09:00</ReportDateTime>
<EventID>20260619073313</EventID>
<InfoType>発表</InfoType>
<Serial>1</Serial>
<InfoKind>地震情報</InfoKind>
<InfoKindVersion>1.0_1</InfoKindVersion>
</Head>
<Body xmlns="http://xml.kishou.go.jp/jmaxml1/body/seismology1/" xmlns:jmx_eb="http://xml.kishou.go.jp/jmaxml1/elementBasis1/">
<Earthquake>
<OriginTime>2026-06-19T07:33:00+09:00</OriginTime>
<Hypocenter>
<Area>
<Name>福島県沖</Name>
<Code>289</Code>
</Area>
</Hypocenter>
<jmx_eb:Magnitude type="Mj">4.1</jmx_eb:Magnitude>
</Earthquake>
<Intensity>
<Observation>
<MaxInt>1</MaxInt>
<Pref><Name>福島県</Name><MaxInt>1</MaxInt>
<Area><Name>福島県中通り</Name><MaxInt>1</MaxInt></Area>
</Pref>
</Observation>
</Intensity>
</Body>
</Report>
"""


def main():
    db_path = "sample_reports.db"

    # 既存のDBがあれば削除
    if os.path.exists(db_path):
        os.remove(db_path)

    print("=" * 60)
    print("  JMAXML SDK SQLite保存サンプル")
    print("=" * 60)

    # Storageの初期化
    print("\n[1] Storageの初期化")
    print("-" * 40)
    storage = SqliteStorage(db_path)
    print(f"  DBパス: {db_path}")
    print(f"  初期レポート数: {storage.count()}")

    # レポートの保存
    print("\n[2] レポートの保存")
    print("-" * 40)
    report = parse(EARTHQUAKE_XML)
    storage.save(report)
    print(f"  保存完了: {report.title}")
    print(f"  イベントID: {report.event_id}")
    print(f"  保存後レポート数: {storage.count()}")

    # レポートの取得
    print("\n[3] レポートの取得")
    print("-" * 40)
    retrieved = storage.get(report.event_id)
    if retrieved:
        print(f"  取得成功: {retrieved.title}")
        print(f"  イベントID: {retrieved.event_id}")
        if isinstance(retrieved, EarthquakeReport):
            print(f"  震源: {retrieved.epicenter}")
            print(f"  M: {retrieved.magnitude}")

    # 全レポート一覧
    print("\n[4] 全レポート一覧")
    print("-" * 40)
    all_reports = storage.list_all()
    print(f"  総件数: {len(all_reports)}")
    for r in all_reports:
        print(f"  - {r.title} ({r.event_id})")

    # 検索
    print("\n[5] 検索")
    print("-" * 40)
    start = datetime.now() - timedelta(hours=1)
    search_results = storage.search(start_date=start)
    print(f"  直近1時間のレポート数: {len(search_results)}")

    # Clientと連携
    print("\n[6] Clientと連携")
    print("-" * 40)
    client = Client()
    client.enable_storage(db_path)
    print(f"  Storage有効化完了")
    print(f"  DBのレポート数: {client._storage.count()}")

    # レポート削除
    print("\n[7] レポート削除")
    print("-" * 40)
    deleted = storage.delete(report.event_id)
    print(f"  削除成功: {deleted}")
    print(f"  削除後レポート数: {storage.count()}")

    print(f"\n  DBファイル: {db_path} (手動で削除してください)")

    print("\n完了!")


if __name__ == "__main__":
    main()

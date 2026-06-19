"""レポート通知判定サンプル - レポートの通知可否を判定"""

from datetime import datetime
from jmaxml import (
    parse,
    check_report,
    notify,
    EarthquakeReport,
    TsunamiReport,
    WeatherWarningReport,
    Warning,
)

EARTHQUAKE_LOW_XML = """<?xml version="1.0" encoding="UTF-8"?>
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

EARTHQUAKE_HIGH_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://xml.kishou.go.jp/jmaxml1/">
<Control>
<Title>震度速報</Title>
<DateTime>2026-06-18T22:00:00Z</DateTime>
<Status>通常</Status>
<EditorialOffice>気象庁本庁</EditorialOffice>
<PublishingOffice>気象庁</PublishingOffice>
</Control>
<Head xmlns="http://xml.kishou.go.jp/jmaxml1/informationBasis1/">
<Title>震度速報</Title>
<ReportDateTime>2026-06-19T06:00:00+09:00</ReportDateTime>
<EventID>20260619060000</EventID>
<InfoType>発表</InfoType>
<Serial>1</Serial>
<InfoKind>震度速報</InfoKind>
<InfoKindVersion>1.0_1</InfoKindVersion>
</Head>
<Body xmlns="http://xml.kishou.go.jp/jmaxml1/body/seismology1/">
<Intensity>
<Observation>
<MaxInt>6強</MaxInt>
<Pref><Name>宮城県</Name><MaxInt>6強</MaxInt>
<Area><Name>宮城県北部</Name><MaxInt>6強</MaxInt></Area>
</Pref>
<Pref><Name>福島県</Name><MaxInt>5強</MaxInt>
<Area><Name>福島県中通り</Name><MaxInt>5強</MaxInt></Area>
</Pref>
</Observation>
</Intensity>
</Body>
</Report>
"""


def main():
    print("=" * 60)
    print("  JMAXML SDK レポート通知判定サンプル")
    print("=" * 60)

    # 低い震度の地震（通知不要）
    print("\n[1] 震度1の地震情報（通知不要）")
    print("-" * 40)
    report_low = parse(EARTHQUAKE_LOW_XML)
    should_notify = check_report(report_low)
    print(f"  タイトル: {report_low.title}")
    if isinstance(report_low, EarthquakeReport):
        print(f"  震源: {report_low.epicenter}")
        print(f"  最大震度: {report_low.max_intensity}")
    print(f"  通知判定: {'通知する' if should_notify else '通知不要'}")

    # 高い震度の地震（通知必要）
    print("\n[2] 震度6強の地震情報（通知必要）")
    print("-" * 40)
    report_high = parse(EARTHQUAKE_HIGH_XML)
    should_notify = check_report(report_high)
    print(f"  タイトル: {report_high.title}")
    if isinstance(report_high, EarthquakeReport):
        print(f"  最大震度: {report_high.max_intensity}")
    print(f"  通知判定: {'通知する' if should_notify else '通知不要'}")

    # プログラムで作成した地震レポート
    print("\n[3] プログラムで作成した地震レポート")
    print("-" * 40)
    earthquake = EarthquakeReport(
        title="テスト地震情報",
        event_id="test_001",
        report_datetime=datetime.now(),
        epicenter="南海トラフ",
        magnitude=8.0,
        max_intensity="7",
    )
    should_notify = check_report(earthquake)
    print(f"  タイトル: {earthquake.title}")
    print(f"  震源: {earthquake.epicenter}")
    print(f"  マグニチュード: M{earthquake.magnitude}")
    print(f"  最大震度: {earthquake.max_intensity}")
    print(f"  通知判定: {'通知する' if should_notify else '通知不要'}")

    # 津波警報
    print("\n[4] 津波警報レポート")
    print("-" * 40)
    tsunami = TsunamiReport(
        title="津波警報",
        event_id="tsunami_001",
        report_datetime=datetime.now(),
        warning_level="津波警報",
    )
    should_notify = check_report(tsunami)
    print(f"  タイトル: {tsunami.title}")
    print(f"  警報レベル: {tsunami.warning_level}")
    print(f"  通知判定: {'通知する' if should_notify else '通知不要'}")

    # 気象警報
    print("\n[5] 気象警報レポート")
    print("-" * 40)
    warning = WeatherWarningReport(
        title="暴風警報",
        event_id="warning_001",
        report_datetime=datetime.now(),
        warnings=[Warning(name="暴風警報", area="東京都")],
    )
    should_notify = check_report(warning)
    print(f"  タイトル: {warning.title}")
    print(f"  警報: {warning.warnings[0].name} ({warning.warnings[0].area})")
    print(f"  通知判定: {'通知する' if should_notify else '通知不要'}")

    # 通知送信テスト
    print("\n[6] 通知送信テスト")
    print("-" * 40)
    result = notify(earthquake, title="テスト通知")
    print(f"  通知結果: {'成功' if result else '失敗/未対応'}")
    print("  (win10toast未インストールの場合はPowerShell通知を試行)")

    print("\n完了!")


if __name__ == "__main__":
    main()

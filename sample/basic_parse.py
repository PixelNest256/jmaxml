"""基本パースサンプル - 気象庁XMLをパースして情報を表示"""

from jmaxml import parse, EarthquakeReport, TsunamiReport, WeatherWarningReport

# サンプルXML（実際の気象庁フォーマット）
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
<Area><Name>福島県浜通り</Name><MaxInt>1</MaxInt></Area>
</Pref>
</Observation>
</Intensity>
</Body>
</Report>
"""

TSUNAMI_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://xml.kishou.go.jp/jmaxml1/">
<Control>
<Title>津波警報・注意報・調査中</Title>
<DateTime>2026-06-18T22:00:00Z</DateTime>
<Status>通常</Status>
<EditorialOffice>気象庁本庁</EditorialOffice>
<PublishingOffice>気象庁</PublishingOffice>
</Control>
<Head xmlns="http://xml.kishou.go.jp/jmaxml1/informationBasis1/">
<Title>津波警報</Title>
<ReportDateTime>2026-06-19T06:00:00+09:00</ReportDateTime>
<EventID>20260619060000</EventID>
<InfoType>発表</InfoType>
<Serial>1</Serial>
<InfoKind>津波情報</InfoKind>
<InfoKindVersion>1.0_1</InfoKindVersion>
</Head>
<Body xmlns="http://xml.kishou.go.jp/jmaxml1/body/seismology1/">
<Tsunami>
<Category>津波警報</Category>
<Area>
<Name>宮城県</Name>
<Code>340</Code>
<ArrivalTime>2026-06-19T07:00:00+09:00</ArrivalTime>
<Height>3m</Height>
<Category>津波警報</Category>
</Area>
<Area>
<Name>福島県</Name>
<Code>280</Code>
<ArrivalTime>2026-06-19T07:10:00+09:00</ArrivalTime>
<Height>2m</Height>
<Category>津波警報</Category>
</Area>
</Tsunami>
</Body>
</Report>
"""


def main():
    print("=" * 60)
    print("  JMAXML SDK 基本パースサンプル")
    print("=" * 60)

    # 地震情報のパース
    print("\n[1] 地震情報のパース")
    print("-" * 40)
    report = parse(EARTHQUAKE_XML)
    print(f"  タイプ: {type(report).__name__}")
    print(f"  タイトル: {report.title}")
    print(f"  イベントID: {report.event_id}")
    print(f"  レポート時刻: {report.report_datetime}")

    if isinstance(report, EarthquakeReport):
        print(f"  震源: {report.epicenter}")
        print(f"  マグニチュード: M{report.magnitude}")
        print(f"  最大震度: {report.max_intensity}")
        print(f"  影響エリア数: {len(report.areas)}")
        for area in report.areas:
            print(f"    - {area.name}: 震度{area.intensity}")

    # 津波情報のパース
    print("\n[2] 津波情報のパース")
    print("-" * 40)
    tsunami_report = parse(TSUNAMI_XML)
    print(f"  タイプ: {type(tsunami_report).__name__}")
    print(f"  タイトル: {tsunami_report.title}")

    if isinstance(tsunami_report, TsunamiReport):
        print(f"  警報レベル: {tsunami_report.warning_level}")
        print(f"  影響エリア数: {len(tsunami_report.areas)}")
        for area in tsunami_report.areas:
            print(f"    - {area.name}: 到達予想時刻={area.first_wave_time}, 予想高さ={area.first_wave_height}")

    # JSON変換
    print("\n[3] JSON変換")
    print("-" * 40)
    json_str = report.to_json(indent=2)
    print(json_str[:500] + "..." if len(json_str) > 500 else json_str)

    print("\n完了!")


if __name__ == "__main__":
    main()

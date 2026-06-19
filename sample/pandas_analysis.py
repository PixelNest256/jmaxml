"""Pandas連携サンプル - レポートをDataFrameに変換して分析"""

from jmaxml import parse, to_dataframe, reports_to_dataframe, EarthquakeReport

EARTHQUAKE_XML_1 = """<?xml version="1.0" encoding="UTF-8"?>
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
<Pref><Name>宮城県</Name><MaxInt>1</MaxInt>
<Area><Name>宮城県南部</Name><MaxInt>1</MaxInt></Area>
</Pref>
</Observation>
</Intensity>
</Body>
</Report>
"""

EARTHQUAKE_XML_2 = """<?xml version="1.0" encoding="UTF-8"?>
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
<MaxInt>5弱</MaxInt>
<Pref><Name>長野県</Name><MaxInt>5弱</MaxInt>
<Area><Name>長野県北部</Name><MaxInt>5弱</MaxInt></Area>
<Area><Name>長野県南部</Name><MaxInt>4</MaxInt></Area>
</Pref>
<Pref><Name>群馬県</Name><MaxInt>4</MaxInt>
<Area><Name>群馬県北部</Name><MaxInt>4</MaxInt></Area>
</Pref>
</Observation>
</Intensity>
</Body>
</Report>
"""


def main():
    try:
        import pandas as pd
    except ImportError:
        print("pandasがインストールされていません: pip install pandas")
        return

    print("=" * 60)
    print("  JMAXML SDK Pandas連携サンプル")
    print("=" * 60)

    # 単一レポートのDataFrame変換
    print("\n[1] 単一レポートのDataFrame変換")
    print("-" * 40)
    report = parse(EARTHQUAKE_XML_1)
    df = to_dataframe(report)
    print(f"  DataFrame形状: {df.shape}")
    print(f"  カラム: {list(df.columns)}")
    print(df.to_string(index=False))

    # 複数レポートのDataFrame変換
    print("\n[2] 複数レポートのDataFrame変換")
    print("-" * 40)
    report1 = parse(EARTHQUAKE_XML_1)
    report2 = parse(EARTHQUAKE_XML_2)
    df_multi = reports_to_dataframe([report1, report2])
    print(f"  DataFrame形状: {df_multi.shape}")
    print(df_multi[["title", "event_id", "report_type", "area_name", "area_intensity"]].to_string(index=False))

    # 基本統計
    print("\n[3] 基本統計")
    print("-" * 40)
    print(f"  総レポート数: {len(df_multi['event_id'].unique())}")
    print(f"  総エリア数: {len(df_multi)}")
    print(f"  レポート種別:")
    for rtype, count in df_multi["report_type"].value_counts().items():
        print(f"    {rtype}: {count}件")

    # CSV出力
    print("\n[4] CSV出力")
    print("-" * 40)
    output_file = "earthquake_data.csv"
    df_multi.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"  保存先: {output_file}")

    print("\n完了!")


if __name__ == "__main__":
    main()

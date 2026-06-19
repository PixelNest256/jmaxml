"""GeoJSON出力サンプル - レポートをGeoJSON形式に変換"""

import json
from jmaxml import Client, parse, to_geojson, to_geojson_collection, EarthquakeReport

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


def main():
    print("=" * 60)
    print("  JMAXML SDK GeoJSON出力サンプル")
    print("=" * 60)

    # サンプルXMLからGeoJSON生成
    print("\n[1] XMLパースからGeoJSON生成")
    print("-" * 40)
    report = parse(EARTHQUAKE_XML)
    geojson = to_geojson(report)

    print(f"  タイプ: {geojson['type']}")
    print(f"  ジオメトリータイプ: {geojson['geometry']['type']}")
    print(f"  座標: {geojson['geometry']['coordinates']}")
    print(f"  プロパティ:")
    for key, value in geojson["properties"].items():
        if key != "areas":
            print(f"    {key}: {value}")
    if "areas" in geojson["properties"]:
        print(f"    areas: {len(geojson['properties']['areas'])}エリア")

    # 複数レポートのコレクション生成
    print("\n[2] 複数レポートのGeoJSONコレクション")
    print("-" * 40)
    client = Client()
    reports = client.fetch_latest("earthquake")

    if reports:
        collection = to_geojson_collection(reports)
        print(f"  タイプ: {collection['type']}")
        print(f"  フィーチャー数: {len(collection['features'])}")

        for i, feature in enumerate(collection["features"][:3], 1):
            props = feature["properties"]
            print(f"\n  [{i}] {props.get('title', 'N/A')}")
            print(f"      座標: {feature['geometry']['coordinates']}")
            if "epicenter" in props:
                print(f"      震源: {props['epicenter']}")
            if "magnitude" in props:
                print(f"      M: {props['magnitude']}")
            if "max_intensity" in props:
                print(f"      最大震度: {props['max_intensity']}")
    else:
        print("  レポートが取得できませんでした")

    # GeoJSONをファイルに保存
    print("\n[3] GeoJSONファイル保存")
    print("-" * 40)
    output_file = "earthquake.geojson"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"  保存先: {output_file}")

    print("\n完了!")


if __name__ == "__main__":
    main()

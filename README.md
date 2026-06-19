# JMAXML SDK

**気象庁防災情報XMLを、直感的なPythonオブジェクトとして扱うためのSDK**

XMLの名前空間や複雑なBody構造を意識せずに、地震・津波・気象警報などの防災情報を `report.max_intensity` や `report.epicenter` のようなシンプルな属性アクセスで取得できます。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-production%2Fstable-brightgreen.svg)](pyproject.toml)

> ⚠️ **このプロジェクトは気象庁とは無関係の非公式OSSです。** 公式配信データ（[気象庁防災情報XML](https://xml.kishou.go.jp/)）を利用していますが、内容の正確性・即時性についてはいかなる保証もありません。実際の防災行動は気象庁・自治体等の公式発表に従ってください。

---

## 目次

- [特徴](#特徴)
- [インストール](#インストール)
- [クイックスタート](#クイックスタート)
- [使い方](#使い方)
  - [基本パース](#基本パース)
  - [Client によるフィード取得](#client-によるフィード取得)
  - [ストリーミング監視（Watcher）](#ストリーミング監視watcher)
  - [SQLiteストレージ](#sqliteストレージ)
  - [JSON変換](#json変換)
  - [Pandas連携](#pandas連携)
  - [GeoJSON出力](#geojson出力)
  - [Windows通知](#windows通知)
  - [FastAPI連携](#fastapi連携)
- [CLI](#cli)
- [対応している電文種別](#対応している電文種別)
- [データモデル](#データモデル)
- [APIリファレンス](#apiリファレンス)
- [プロジェクト構成](#プロジェクト構成)
- [開発](#開発)
- [ロードマップ・既知の制限](#ロードマップ既知の制限)
- [ライセンス](#ライセンス)

---

## 特徴

- 🗂️ **シンプルなAPI** — `parse(xml_text)` だけでXMLをPythonオブジェクトに変換
- 🔒 **型安全なデータモデル** — `dataclass` ベースの `EarthquakeReport` / `TsunamiReport` / `WeatherWarningReport` などでIDE補完が効く
- 📡 **フィード取得・監視** — 気象庁Atomフィードの取得、同期/非同期ストリーミング監視（`watch()` / `awatch()`）
- 💾 **SQLite永続化** — 取得した電文を保存し、期間・種別で検索
- 🔁 **エコシステム連携** — Pandas（DataFrame変換）、GeoJSON出力、Windowsトースト通知、FastAPI Web API化を標準サポート
- 🖥️ **CLI同梱** — `jmaxml` コマンドでターミナルから即利用可能

## インストール

```bash
pip install jmaxml

# オプション機能
pip install jmaxml[pandas]    # Pandas連携 (to_dataframe / reports_to_dataframe)
pip install jmaxml[fastapi]   # FastAPI連携 (create_app)
pip install jmaxml[notify]    # Windowsトースト通知 (win11toast)
pip install jmaxml[all]       # 全機能
```

対応Pythonバージョン: **3.10以上**

## クイックスタート

```python
from jmaxml import Client

client = Client()
reports = client.fetch_recent()

for report in reports:
    print(report.title, report.report_datetime)
```

## 使い方

### 基本パース

XML文字列を直接パースして、地震・津波・気象警報の各レポートオブジェクトを取得します。

```python
from jmaxml import parse, EarthquakeReport

report = parse(xml_text)

if isinstance(report, EarthquakeReport):
    print(report.epicenter)       # 震源地名
    print(report.magnitude)       # マグニチュード
    print(report.max_intensity)   # 最大震度
    for area in report.areas:
        print(area.name, area.intensity)
```

### Client によるフィード取得

`Client` は気象庁Atomフィードの取得からXMLダウンロード・パースまでを一括して行います。

```python
from jmaxml import Client, EarthquakeReport

client = Client()

# フィードの種別を指定して最新10件を取得・パース
reports = client.fetch_latest("earthquake")

# 直近24時間分を取得（report_typeでフィルタ可能）
reports = client.fetch_recent(hours=24, report_type="earthquake")

# イベントIDから直接取得
report = client.get_event("20260619073313")

for report in reports:
    if isinstance(report, EarthquakeReport):
        print(report.epicenter, report.magnitude, report.max_intensity)
```

利用可能なフィード種別: `earthquake` / `weather` / `regular` / `other` / `all`

### ストリーミング監視（Watcher）

新着電文をポーリングして逐次処理します。同期・非同期の両方に対応しています。

```python
# 同期版
for report in client.watch(feed_type="earthquake", interval=60):
    print(report.title)

# 非同期版
async for report in client.awatch(feed_type="earthquake", interval=60):
    print(report.title)
```

### SQLiteストレージ

取得したレポートをSQLiteに保存し、後から検索できます。

```python
client = Client()
client.enable_storage("reports.db")

reports = client.fetch_latest()           # 取得と同時に自動保存
reports = client.search(
    start_date=datetime(2026, 1, 1),
    end_date=datetime(2026, 12, 31),
    report_type="earthquake",
)
```

`SqliteStorage` を直接利用することも可能です（`save` / `get` / `search` / `list_all` / `count` / `delete` / `clear`）。

### JSON変換

```python
report = client.fetch_latest()[0]
print(report.to_json(indent=2))
```

### Pandas連携

```python
from jmaxml import Client, to_dataframe, reports_to_dataframe

client = Client()
reports = client.fetch_recent()

df = to_dataframe(reports[0])        # 単一レポート → DataFrame（エリア単位で行展開）
df = reports_to_dataframe(reports)   # 複数レポートを連結したDataFrame
```

### GeoJSON出力

地震情報の震源地、気象警報の対象エリアなどを地図表示に利用できる形式で出力します（主要都道府県の概算座標を内蔵）。

```python
from jmaxml import Client, to_geojson, to_geojson_collection

client = Client()
reports = client.fetch_recent()

geojson = to_geojson(reports[0])              # 単一レポート → Feature
geojson = to_geojson_collection(reports)      # 複数レポート → FeatureCollection
```

### Windows通知

震度・警報レベルに応じて通知が必要かを判定し、Windowsのトースト通知を送信します（`win11toast` → `win10toast` の順にフォールバック、Windows以外では何もせず `False` を返します）。

```python
from jmaxml import parse, notify, check_report

report = parse(xml_text)

if check_report(report):   # 震度3以上、津波警報以上、特別警報・暴風・大雨等のキーワードを検出
    notify(report)
```

### FastAPI連携

SDKをそのままWeb APIとして公開できます。

```python
from jmaxml.fastapi_app import create_app

app = create_app(db_path="reports.db")  # db_path省略時はストレージ無効
# 実行: uvicorn jmaxml.fastapi_app:app --reload
```

| エンドポイント | 説明 |
|---|---|
| `GET /api/reports/latest` | 最新電文を取得（`feed_type`, `limit`） |
| `GET /api/reports/recent` | 直近N時間の電文を取得（`hours`, `report_type`） |
| `GET /api/reports/{event_id}` | イベントIDで取得 |
| `GET /api/reports` | SQLite検索（`start_date`, `end_date`, `report_type`） |
| `GET /api/feed` | Atomフィードのエントリ一覧 |

## CLI

```bash
jmaxml latest                       # 最新電文を取得（--type, --json, --limit）
jmaxml earthquake                   # 地震・津波情報のみ取得
jmaxml volcano                      # 火山・降灰情報のみ取得
jmaxml watch                        # 新着電文をリアルタイム監視（--type, --interval）

jmaxml latest --type weather --json --limit 5
```

## 対応している電文種別

`parse()` はすべての電文タイプを検出しますが、専用パーサーが実装されているのは以下のとおりです。専用パーサー未対応の種別は `BaseReport`（タイトル・イベントID・日時のみ）として返されます。

| 電文種別 | `ReportType` | 専用パーサー | 主なフィールド |
|---|---|:---:|---|
| 震度速報・震源震度情報 | `earthquake` | ✅ | `epicenter`, `magnitude`, `depth_km`, `max_intensity`, `areas` |
| 津波警報・注意報 | `tsunami` | ✅ | `warning_level`, `areas`（到達時刻・高さ・カテゴリ） |
| 気象警報・注意報 / 特別警報 | `weather_warning` / `special_warning` | ✅ | `warnings`（警報名・対象エリア） |
| 台風情報 | `typhoon` | 検出のみ | `title`, `event_id`, `report_datetime` |
| 火山情報・降灰予報 | `volcano` / `ashfall` | 検出のみ | 〃 |
| 天気予報・気象情報・海上予報・早期注意情報 | `weather_forecast` / `weather_info` / `marine_forecast` / `early_warning` | 検出のみ | 〃 |

## データモデル

```text
BaseReport
├── EarthquakeReport     (epicenter, magnitude, depth_km, max_intensity, areas)
├── TsunamiReport        (warning_level, areas)
└── WeatherWarningReport (warnings)
```

すべてのレポートは `to_dict()` / `to_json()` をサポートします。

## APIリファレンス

| メソッド / 関数 | 説明 |
|---|---|
| `parse(xml)` | XML文字列・バイト列をレポートオブジェクトへ変換 |
| `Client.fetch_feed(feed_type)` | Atomフィードのエントリ一覧を取得 |
| `Client.fetch_latest(feed_type)` | 最新電文を取得・パース（先頭10件） |
| `Client.fetch_recent(hours, report_type)` | 直近N時間分の電文を取得 |
| `Client.get_event(event_id)` | イベントIDから電文を取得 |
| `Client.watch(feed_type, interval)` | 同期ストリーミング監視 |
| `Client.awatch(feed_type, interval)` | 非同期ストリーミング監視 |
| `Client.enable_storage(db_path)` | SQLite永続化を有効化 |
| `Client.search(start_date, end_date, report_type)` | SQLiteから検索（要 `enable_storage`） |
| `to_dataframe(report)` / `reports_to_dataframe(reports)` | Pandas DataFrameへ変換 |
| `to_geojson(report)` / `to_geojson_collection(reports)` | GeoJSON Feature / FeatureCollectionへ変換 |
| `notify(report)` | Windowsトースト通知を送信 |
| `check_report(report)` | 通知すべき重要度かどうかを判定 |
| `create_app(db_path)` | FastAPIアプリを生成 |

## プロジェクト構成

```text
jmaxml/
├─ client.py          # Client（SDKのメインエントリポイント）
├─ parser/            # XML → モデル変換（電文種別判定を含む）
├─ models/             # dataclassベースのレポートモデル
├─ feed/               # Atomフィード取得 (FeedClient) と監視 (Watcher / AsyncWatcher)
├─ storage/            # SQLite永続化 (SqliteStorage)
├─ pandas.py           # Pandas連携
├─ geojson.py          # GeoJSON出力
├─ notify.py           # Windows通知
├─ fastapi_app.py      # FastAPI Web API
└─ cli/                # `jmaxml` コマンド実装

sample/    # 用途別の実行サンプル（パース／監視／通知／Pandas／GeoJSON／ストレージ）
tests/     # pytestテストスイート
```

## 開発

```bash
git clone https://github.com/Kasam/jmaxml.git
cd jmaxml
pip install -e .[all]

pytest               # テスト実行
python sample/basic_parse.py          # サンプル実行例
```

## ロードマップ・既知の制限

- 台風・火山・天気予報系の電文は現在 `ReportType` の判定のみ対応しており、専用フィールドの抽出は未実装です（`TyphoonReport` / `VolcanoReport` 等は今後追加予定）
- 震源の深さ（`depth_km`）はモデルにフィールドはあるものの、現状のパーサーでは未抽出です
- 主要都道府県の概算座標による簡易ジオコーディングのため、GeoJSON出力の座標は厳密な震源位置ではありません

## ライセンス

MIT License — 詳細は [LICENSE](LICENSE) を参照してください。

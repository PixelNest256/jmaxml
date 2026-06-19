"""Windows通知テスト - 通知機能の動作確認"""

import sys
from datetime import datetime
from jmaxml import (
    EarthquakeReport,
    TsunamiReport,
    WeatherWarningReport,
    Warning,
)
from jmaxml.notify import notify, check_report, _build_title, _build_body


def test_build_messages():
    print("[1] 通知メッセージの組み立てテスト")
    print("-" * 40)

    # 地震情報
    eq = EarthquakeReport(
        title="震度速報",
        event_id="test_eq",
        report_datetime=datetime.now(),
        epicenter="福島県沖",
        magnitude=7.2,
        max_intensity="6強",
    )
    print(f"  地震タイトル: {_build_title(eq)}")
    print(f"  地震本文: {_build_body(eq)}")

    # 津波情報
    ts = TsunamiReport(
        title="津波警報",
        event_id="test_ts",
        report_datetime=datetime.now(),
        warning_level="津波警報",
    )
    print(f"  津波タイトル: {_build_title(ts)}")
    print(f"  津波本文: {_build_body(ts)}")

    # 気象警報
    ww = WeatherWarningReport(
        title="暴風警報",
        event_id="test_ww",
        report_datetime=datetime.now(),
        warnings=[Warning(name="暴風警報", area="東京都"), Warning(name="大雨注意報", area="神奈川県")],
    )
    print(f"  警報タイトル: {_build_title(ww)}")
    print(f"  警報本文: {_build_body(ww)}")


def test_check_reports():
    print("\n[2] 通知判定テスト")
    print("-" * 40)

    # 震度1 → 通知不要
    eq_low = EarthquakeReport(
        title="テスト", event_id="1", report_datetime=datetime.now(),
        epicenter="テスト", magnitude=3.0, max_intensity="1",
    )
    print(f"  震度1: {check_report(eq_low)} (期待: False)")

    # 震度3 → 通知必要
    eq_mid = EarthquakeReport(
        title="テスト", event_id="2", report_datetime=datetime.now(),
        epicenter="テスト", magnitude=5.0, max_intensity="3",
    )
    print(f"  震度3: {check_report(eq_mid)} (期待: True)")

    # 震度6強 → 通知必要
    eq_high = EarthquakeReport(
        title="テスト", event_id="3", report_datetime=datetime.now(),
        epicenter="テスト", magnitude=7.0, max_intensity="6強",
    )
    print(f"  震度6強: {check_report(eq_high)} (期待: True)")

    # 津波警報 → 通知必要
    ts = TsunamiReport(
        title="テスト", event_id="4", report_datetime=datetime.now(),
        warning_level="津波警報",
    )
    print(f"  津波警報: {check_report(ts)} (期待: True)")

    # 暴風警報 → 通知必要
    ww = WeatherWarningReport(
        title="テスト", event_id="5", report_datetime=datetime.now(),
        warnings=[Warning(name="暴風警報", area="東京都")],
    )
    print(f"  暴風警報: {check_report(ww)} (期待: True)")


def test_send_notification():
    print("\n[3] 実際の通知送信テスト")
    print("-" * 40)
    print(f"  プラットフォーム: {sys.platform}")

    eq = EarthquakeReport(
        title="テスト地震情報",
        event_id="test_notify",
        report_datetime=datetime.now(),
        epicenter="南海トラフ",
        magnitude=8.0,
        max_intensity="7",
    )

    print(f"  通知タイトル: {_build_title(eq)}")
    print(f"  通知本文: {_build_body(eq)}")
    print(f"\n  通知を送信します...")

    result = notify(eq, title="JMAXML テスト通知")
    print(f"  送信結果: {'成功' if result else '失敗'}")

    if result:
        print(f"  デスクトップに通知が表示されましたか？")
    else:
        print(f"  通知の送信に失敗しました")
        if sys.platform != "win32":
            print(f"  (Windows以外のプラットフォームでは通知非対応です)")
        else:
            print(f"  (win10toastまたはPowerShell Toastのいずれも利用できません)")


def test_send_various():
    print("\n[4] 各種レポートの通知送信")
    print("-" * 40)

    reports = [
        ("地震情報", EarthquakeReport(
            title="地震情報", event_id="eq1", report_datetime=datetime.now(),
            epicenter="福島県沖", magnitude=5.5, max_intensity="5強",
        )),
        ("津波警報", TsunamiReport(
            title="津波警報", event_id="ts1", report_datetime=datetime.now(),
            warning_level="津波警報",
        )),
        ("暴風警報", WeatherWarningReport(
            title="暴風警報", event_id="ww1", report_datetime=datetime.now(),
            warnings=[Warning(name="暴風警報", area="東京都")],
        )),
    ]

    for name, report in reports:
        print(f"\n  --- {name} ---")
        print(f"  タイトル: {_build_title(report)}")
        print(f"  本文: {_build_body(report)}")
        result = notify(report, title=f"JMAXML - {name}")
        print(f"  送信: {'成功' if result else '失敗'}")


if __name__ == "__main__":
    print("=" * 60)
    print("  JMAXML SDK Windows通知テスト")
    print("=" * 60)

    test_build_messages()
    test_check_reports()
    test_send_notification()
    test_send_various()

    print("\n" + "=" * 60)
    print("  テスト完了!")
    print("=" * 60)

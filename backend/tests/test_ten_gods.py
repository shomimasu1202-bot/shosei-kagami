"""通変星（十神）と今年の運勢のユニットテスト。"""

from __future__ import annotations

import datetime as dt

import pytest

from app.engine import TEN_GODS, get_ten_god, get_reading, STEMS


# 天干: 甲0 乙1 丙2 丁3 戊4 己5 庚6 辛7 壬8 癸9
def _i(name: str) -> int:
    return STEMS.index(name)


# ---------------------------------------------------------------------------
# 1. 通変星の定義（甲＝日主で全ケースを検証）
# ---------------------------------------------------------------------------

def test_ten_god_from_kinoe() -> None:
    # 日主 甲（木・陽）から見た各天干の通変星。
    cases = {
        "甲": "比肩",  # 同五行・同陰陽
        "乙": "劫財",  # 同五行・異陰陽
        "丙": "食神",  # 木生火・同陽
        "丁": "傷官",  # 木生火・異陰陽
        "戊": "偏財",  # 木剋土・同陽
        "己": "正財",  # 木剋土・異陰陽
        "庚": "偏官",  # 金剋木・同陽
        "辛": "正官",  # 金剋木・異陰陽
        "壬": "偏印",  # 水生木・同陽
        "癸": "印綬",  # 水生木・異陰陽
    }
    for stem, god in cases.items():
        assert get_ten_god(_i("甲"), _i(stem)) == god


def test_self_is_hiken() -> None:
    for i in range(10):
        assert get_ten_god(i, i) == "比肩"  # 自分自身は必ず比肩


def test_all_results_are_valid_ten_gods() -> None:
    seen = set()
    for dm in range(10):
        for t in range(10):
            g = get_ten_god(dm, t)
            assert g in TEN_GODS
            seen.add(g)
    assert seen == set(TEN_GODS)  # 10種すべて出現し得る


def test_biken_gozai_are_same_element() -> None:
    # 比肩・劫財は必ず日主と同じ五行（index//2 が一致）。
    for dm in range(10):
        for t in range(10):
            if get_ten_god(dm, t) in ("比肩", "劫財"):
                assert dm // 2 == t // 2


# ---------------------------------------------------------------------------
# 2. 今年の運勢セクション
# ---------------------------------------------------------------------------

def test_year_fortune_section_present() -> None:
    r = get_reading(dt.date(1990, 4, 15), reference_date=dt.date(2026, 6, 1))
    yf = r.year_fortune
    assert yf is not None
    # 2026年（立春後）は 丙午。
    assert yf["year_ganzhi"] == "丙午"
    assert yf["astrological_year"] == 2026
    assert yf["ten_god"] in TEN_GODS
    # 末尾セクションに反映される
    fortune = [s for s in r.sections if s.section_id == "fortune_year"][0]
    assert yf["year_ganzhi"] in fortune.text
    assert yf["ten_god"] in fortune.text
    assert fortune.text.endswith("。")


def test_year_fortune_matches_ten_god_of_ryunen() -> None:
    # 1990-04-15 は日干 庚（金・陽）。2026 流年の年干 丙（火・陽）。
    # 火剋金（剋我）＋同陰陽 → 偏官。
    r = get_reading(dt.date(1990, 4, 15), reference_date=dt.date(2026, 6, 1))
    assert get_ten_god(_i("庚"), _i("丙")) == "偏官"
    assert r.year_fortune["ten_god"] == "偏官"


def test_year_fortune_changes_with_reference_year() -> None:
    a = get_reading(dt.date(1990, 4, 15), reference_date=dt.date(2026, 6, 1))  # 丙午
    b = get_reading(dt.date(1990, 4, 15), reference_date=dt.date(2027, 6, 1))  # 丁未
    assert a.year_fortune["year_ganzhi"] != b.year_fortune["year_ganzhi"]


def test_reading_json_serializable_with_fortune() -> None:
    import json
    r = get_reading(dt.datetime(1988, 11, 3, 10, 0), reference_date=dt.date(2026, 6, 1))
    json.dumps(r.to_dict(), ensure_ascii=False)

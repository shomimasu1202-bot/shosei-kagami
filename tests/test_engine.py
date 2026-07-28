"""掌星鑑 Phase 1 エンジンのユニットテスト。"""

from __future__ import annotations

import datetime as dt

import pytest

from app.engine import (
    STEMS,
    BRANCHES,
    STEM_TO_ELEMENT,
    STEM_TO_YINYANG,
    BRANCH_TO_ELEMENT,
    TYPE_TABLE,
    get_day_pillar,
    get_five_element_profile,
    get_type,
)


# ---------------------------------------------------------------------------
# 1. アンカー / 既知の日干支
# ---------------------------------------------------------------------------

# (日付, 期待する日干支名) — 外部の万年暦で確認できる基準点。
#   2000-01-07 = 甲子  … 本実装のアンカー（60干支の先頭）
#   1900-01-01 = 甲戌  … 古典的な基準日（多くの干支表で確認可能）
#   2000-01-01 = 戊午  … JDN換算式 (JDN+9)%10 / (JDN+1)%12 と一致
KNOWN_GANZHI = [
    (dt.date(2000, 1, 7), "甲子"),
    (dt.date(1900, 1, 1), "甲戌"),
    (dt.date(2000, 1, 1), "戊午"),
]


@pytest.mark.parametrize("date, expected", KNOWN_GANZHI)
def test_known_ganzhi_dates(date: dt.date, expected: str) -> None:
    pillar = get_day_pillar(date)
    assert pillar.ganzhi_name == expected


def test_anchor_is_kinoe_ne() -> None:
    """アンカー 2000-01-07 は 甲子（index 0/0, 60サイクル先頭）。"""
    pillar = get_day_pillar(dt.date(2000, 1, 7))
    assert pillar.day_stem_index == 0
    assert pillar.day_branch_index == 0
    assert pillar.day_stem_name == "甲"
    assert pillar.day_branch_name == "子"
    assert pillar.ganzhi60_index == 0


# ---------------------------------------------------------------------------
# 2. 60日周期の循環
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "start",
    [dt.date(2000, 1, 7), dt.date(1987, 6, 15), dt.date(2024, 12, 31)],
)
def test_60_day_cycle_repeats(start: dt.date) -> None:
    base = get_day_pillar(start)
    same = get_day_pillar(start + dt.timedelta(days=60))
    diff = get_day_pillar(start + dt.timedelta(days=30))
    assert base.ganzhi_name == same.ganzhi_name
    assert base.ganzhi_name != diff.ganzhi_name


def test_consecutive_days_advance_by_one() -> None:
    """連続する日は 60干支インデックスが 1 ずつ進む。"""
    d = dt.date(2000, 1, 7)
    for i in range(70):
        expected = i % 60
        assert get_day_pillar(d + dt.timedelta(days=i)).ganzhi60_index == expected


# ---------------------------------------------------------------------------
# 3. 境界（うるう年・月末・年末年始）
# ---------------------------------------------------------------------------

def _consecutive(a: dt.date, b: dt.date) -> bool:
    """b は a の翌日干支か（60サイクルで +1）。"""
    ia = get_day_pillar(a).ganzhi60_index
    ib = get_day_pillar(b).ganzhi60_index
    return ib == (ia + 1) % 60


def test_leap_day_boundary_2000() -> None:
    """2000年はうるう年。2/28 → 2/29 → 3/1 が干支上で連続する。"""
    assert _consecutive(dt.date(2000, 2, 28), dt.date(2000, 2, 29))
    assert _consecutive(dt.date(2000, 2, 29), dt.date(2000, 3, 1))


def test_non_leap_day_boundary_2001() -> None:
    """2001年は非うるう年。2/28 の翌日は 3/1 で連続する。"""
    assert _consecutive(dt.date(2001, 2, 28), dt.date(2001, 3, 1))


def test_year_end_boundary() -> None:
    """年末年始（12/31 → 翌1/1）が連続する。"""
    assert _consecutive(dt.date(1999, 12, 31), dt.date(2000, 1, 1))
    assert _consecutive(dt.date(2023, 12, 31), dt.date(2024, 1, 1))


def test_month_end_boundaries() -> None:
    """各月末 → 翌月初が連続する。"""
    ends = [
        (dt.date(2023, 1, 31), dt.date(2023, 2, 1)),
        (dt.date(2023, 4, 30), dt.date(2023, 5, 1)),
        (dt.date(2024, 2, 29), dt.date(2024, 3, 1)),  # うるう年
    ]
    for a, b in ends:
        assert _consecutive(a, b)


# ---------------------------------------------------------------------------
# 4. 深夜（子の刻）境界オプション
# ---------------------------------------------------------------------------

def test_late_night_boundary_shifts_to_next_day() -> None:
    naive = dt.datetime(2000, 1, 7, 23, 30)  # 23:30
    same_day = get_day_pillar(naive, late_night_boundary=False)
    next_day = get_day_pillar(naive, late_night_boundary=True)
    assert same_day.ganzhi_name == get_day_pillar(dt.date(2000, 1, 7)).ganzhi_name
    assert next_day.ganzhi_name == get_day_pillar(dt.date(2000, 1, 8)).ganzhi_name


def test_late_night_boundary_before_23_unchanged() -> None:
    naive = dt.datetime(2000, 1, 7, 22, 59)
    assert (
        get_day_pillar(naive, late_night_boundary=True).ganzhi_name
        == get_day_pillar(dt.date(2000, 1, 7)).ganzhi_name
    )


def test_pure_date_ignores_late_night_flag() -> None:
    d = dt.date(2000, 1, 7)
    assert (
        get_day_pillar(d, late_night_boundary=True).ganzhi_name
        == get_day_pillar(d, late_night_boundary=False).ganzhi_name
    )


# ---------------------------------------------------------------------------
# 5. 五行・陰陽の判定
# ---------------------------------------------------------------------------

def test_stem_element_table() -> None:
    expected = ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水"]
    for i, e in enumerate(expected):
        assert STEM_TO_ELEMENT[i] == e


def test_stem_yinyang_table() -> None:
    # 甲丙戊庚壬=陽（偶数 index）、乙丁己辛癸=陰（奇数 index）
    for i in range(10):
        assert STEM_TO_YINYANG[i] == ("陽" if i % 2 == 0 else "陰")


def test_branch_element_table() -> None:
    expected = {
        "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
        "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
    }
    for idx, name in enumerate(BRANCHES):
        assert BRANCH_TO_ELEMENT[idx] == expected[name]


def test_five_element_profile_for_kinoe() -> None:
    prof = get_five_element_profile(dt.date(2000, 1, 7))  # 甲
    assert prof.五行 == "木"
    assert prof.陰陽 == "陽"


# ---------------------------------------------------------------------------
# 6. 10タイプへの写像
# ---------------------------------------------------------------------------

# 日干 index 0..9 が得られる連続日（アンカー 甲子 起点）。
STEM_DATES = [dt.date(2000, 1, 7) + dt.timedelta(days=i) for i in range(10)]

# 確定表どおりの期待値（stem_index -> (type_id, 名称, 読み, 五行, 陰陽)）
EXPECTED_TYPES = [
    ("you", "葉", "よう", "木", "陽"),      # 甲
    ("fuji", "藤", "ふじ", "木", "陰"),     # 乙
    ("asahi", "旭", "あさひ", "火", "陽"),  # 丙
    ("hotaru", "蛍", "ほたる", "火", "陰"), # 丁
    ("mine", "嶺", "みね", "土", "陽"),     # 戊
    ("sono", "苑", "その", "土", "陰"),     # 己
    ("rin", "鈴", "りん", "金", "陽"),      # 庚
    ("gyoku", "玉", "ぎょく", "金", "陰"),  # 辛
    ("minato", "湊", "みなと", "水", "陽"), # 壬
    ("shizuku", "雫", "しずく", "水", "陰"),# 癸
]


@pytest.mark.parametrize("stem_index", list(range(10)))
def test_type_mapping_matches_table(stem_index: int) -> None:
    date = STEM_DATES[stem_index]
    # 前提: この日の日干が想定の stem_index であること。
    assert get_day_pillar(date).day_stem_index == stem_index

    type_id, name, reading, element, yinyang = EXPECTED_TYPES[stem_index]
    t = get_type(date)
    assert t.type_id == type_id
    assert t.名称 == name
    assert t.読み == reading
    assert t.五行 == element
    assert t.陰陽 == yinyang


def test_explicit_required_examples() -> None:
    """仕様で明示された 甲→葉/木/陽、辛→玉/金/陰、癸→雫/水/陰 を検証。"""
    kinoe = get_type(dt.date(2000, 1, 7))    # 甲
    assert (kinoe.type_id, kinoe.名称, kinoe.五行, kinoe.陰陽) == ("you", "葉", "木", "陽")

    kanoto = get_type(dt.date(2000, 1, 14))  # 辛
    assert (kanoto.type_id, kanoto.名称, kanoto.五行, kanoto.陰陽) == ("gyoku", "玉", "金", "陰")

    mizunoto = get_type(dt.date(2000, 1, 16))  # 癸
    assert (mizunoto.type_id, mizunoto.名称, mizunoto.五行, mizunoto.陰陽) == ("shizuku", "雫", "水", "陰")


def test_type_table_is_one_to_one_and_complete() -> None:
    assert len(TYPE_TABLE) == 10
    assert len({t.type_id for t in TYPE_TABLE}) == 10  # type_id 一意
    assert len(STEMS) == 10


def test_type_table_consistent_with_five_elements() -> None:
    """確定表の五行・陰陽が、十干→五行/陰陽テーブルと矛盾しないこと。"""
    for i, t in enumerate(TYPE_TABLE):
        assert t.五行 == STEM_TO_ELEMENT[i]
        assert t.陰陽 == STEM_TO_YINYANG[i]


# ---------------------------------------------------------------------------
# 7. JSON シリアライズ可能性
# ---------------------------------------------------------------------------

def test_return_values_are_json_serializable() -> None:
    import json

    d = dt.date(1995, 8, 20)
    for obj in (get_day_pillar(d), get_five_element_profile(d), get_type(d)):
        json.dumps(obj.to_dict(), ensure_ascii=False)  # 例外が出なければ OK

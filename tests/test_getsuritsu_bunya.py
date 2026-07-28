"""月律分野蔵干（Phase 2.7+）のユニットテスト。"""

from __future__ import annotations

import datetime as dt

import pytest

from app.engine import (
    get_five_element_balance,
    get_month_solar_term_start,
    find_solar_term,
)
from app.engine.getsuritsu_bunya import (
    GETSURITSU_BUNYA,
    BUNYA_TOTAL_DAYS,
    commanding_stem,
)
from app.engine.hidden_stems import HONKI, CHUKI, YOKI


# ---------------------------------------------------------------------------
# 1. 分野テーブルの健全性
# ---------------------------------------------------------------------------

def test_bunya_covers_all_branches() -> None:
    assert set(GETSURITSU_BUNYA.keys()) == set(range(12))


def test_bunya_days_sum_to_total() -> None:
    for branch, segs in GETSURITSU_BUNYA.items():
        assert sum(days for _, _, days in segs) == BUNYA_TOTAL_DAYS, branch


def test_bunya_order_yoki_to_honki() -> None:
    """余気で始まり本気で終わる。中気は間のみ。"""
    for segs in GETSURITSU_BUNYA.values():
        assert segs[0][1] == YOKI
        assert segs[-1][1] == HONKI
        for _, role, _ in segs[1:-1]:
            assert role == CHUKI


# ---------------------------------------------------------------------------
# 2. commanding_stem: 経過日数で司令が変わる
# ---------------------------------------------------------------------------

def test_commander_by_days_in_tiger_month() -> None:
    # 寅: 戊(余)0-7, 丙(中)7-14, 甲(本)14-30
    assert commanding_stem(2, 1.0) == (4, YOKI)    # 戊
    assert commanding_stem(2, 10.0) == (2, CHUKI)  # 丙
    assert commanding_stem(2, 20.0) == (0, HONKI)  # 甲


def test_commander_clamps_beyond_range() -> None:
    # 30日を超えたら本気に丸める
    assert commanding_stem(2, 40.0) == (0, HONKI)
    # 負値は先頭（余気）
    assert commanding_stem(2, -1.0) == (4, YOKI)


def test_commander_boundary_is_left_closed() -> None:
    # ちょうど7.0日は次の区間（中気 丙）に入る
    assert commanding_stem(2, 6.999) == (4, YOKI)
    assert commanding_stem(2, 7.0) == (2, CHUKI)


# ---------------------------------------------------------------------------
# 3. 節入り起点の算出
# ---------------------------------------------------------------------------

def test_month_setsu_start_is_risshun_for_feb() -> None:
    # 2024-02-10 は立春(2/4)の後 → その月の節入りは立春
    setsu = get_month_solar_term_start(dt.date(2024, 2, 10))
    risshun = find_solar_term(2024, 315.0)
    assert (setsu.year, setsu.month, setsu.day) == (risshun.year, risshun.month, risshun.day)
    assert setsu <= _noon_jst(2024, 2, 10)


def test_month_setsu_start_before_birth() -> None:
    for md in [(2024, 3, 20), (2024, 7, 1), (2025, 1, 10), (2024, 12, 30)]:
        d = dt.date(*md)
        setsu = get_month_solar_term_start(d)
        assert setsu <= _noon_jst(*md)


def _noon_jst(y, m, d):
    from app.engine.solar import JST
    return dt.datetime(y, m, d, 12, 0, tzinfo=JST)


# ---------------------------------------------------------------------------
# 4. バランスへの反映（同じ月でも生まれ日で変わる）
# ---------------------------------------------------------------------------

def test_month_commander_recorded_in_balance() -> None:
    b = get_five_element_balance(dt.date(2024, 2, 6))  # 立春直後＝寅月の余気
    assert b.month_commander is not None
    assert b.month_commander["phase"] == "余気"
    assert b.month_commander["stem"] == "戊"
    assert b.month_commander["element"] == "土"


def test_same_month_different_day_changes_balance() -> None:
    """寅月の前半(余気 戊=土)と後半(本気 甲=木)で分布が変わる。"""
    early = get_five_element_balance(dt.date(2024, 2, 6))   # 余気 戊(土)司令
    late = get_five_element_balance(dt.date(2024, 2, 25))   # 本気 甲(木)司令
    assert early.month_commander["phase"] == "余気"
    assert late.month_commander["phase"] == "本気"
    assert early.month_commander["element"] == "土"
    assert late.month_commander["element"] == "木"
    # 司令が土→木に変わるため、スコア分布も変わる
    assert early.scores != late.scores


def test_bunya_can_be_disabled() -> None:
    with_bunya = get_five_element_balance(dt.date(2024, 2, 6))
    without = get_five_element_balance(dt.date(2024, 2, 6), use_getsuritsu_bunya=False)
    assert with_bunya.month_commander is not None
    assert without.month_commander is None


def test_describe_mentions_commander() -> None:
    from app.engine import describe_balance
    b = get_five_element_balance(dt.date(2024, 2, 6))
    text = describe_balance(b)
    assert "司令" in text or "節入り" in text
    assert text.endswith("。")

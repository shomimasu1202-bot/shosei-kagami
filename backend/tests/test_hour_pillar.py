"""時柱（時干支・五鼠遁）と四柱（Phase 3）のユニットテスト。"""

from __future__ import annotations

import datetime as dt

import pytest

from app.engine import (
    get_hour_pillar,
    get_four_pillars,
    get_day_pillar,
    get_five_element_balance,
)


# ---------------------------------------------------------------------------
# 1. 時支（十二時辰）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "hour, branch",
    [
        (23, "子"), (0, "子"), (1, "丑"), (2, "丑"), (3, "寅"),
        (5, "卯"), (7, "辰"), (9, "巳"), (11, "午"), (12, "午"),
        (13, "未"), (15, "申"), (17, "酉"), (19, "戌"), (21, "亥"), (22, "亥"),
    ],
)
def test_hour_branch_by_clock(hour: int, branch: str) -> None:
    hp = get_hour_pillar(dt.datetime(2000, 1, 7, hour, 30))
    assert hp.hour_branch_name == branch


def test_hour_requires_datetime() -> None:
    with pytest.raises(TypeError):
        get_hour_pillar(dt.date(2000, 1, 7))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 2. 時干（五鼠遁）— 日干 → 子時の天干
# ---------------------------------------------------------------------------

# 2000-01-07 は甲子日。以降の連続日で日干 甲乙丙丁戊己庚辛壬癸 を得る。
# 各日 00:30（子刻・23時前なので日は動かない）の時柱は子時の天干＝五鼠遁。
EXPECTED_RAT = [
    ("甲", "甲子"),  # 甲日 → 甲子
    ("乙", "丙子"),  # 乙日 → 丙子
    ("丙", "戊子"),  # 丙日 → 戊子
    ("丁", "庚子"),  # 丁日 → 庚子
    ("戊", "壬子"),  # 戊日 → 壬子
    ("己", "甲子"),  # 己日 → 甲子
    ("庚", "丙子"),  # 庚日 → 丙子
    ("辛", "戊子"),  # 辛日 → 戊子
    ("壬", "庚子"),  # 壬日 → 庚子
    ("癸", "壬子"),  # 癸日 → 壬子
]


@pytest.mark.parametrize("offset, expected", list(enumerate(EXPECTED_RAT)))
def test_five_rat_rule(offset: int, expected: tuple[str, str]) -> None:
    day_stem, hour_ganzhi = expected
    d = dt.datetime(2000, 1, 7, 0, 30) + dt.timedelta(days=offset)
    assert get_day_pillar(d).day_stem_name == day_stem
    assert get_hour_pillar(d).ganzhi_name == hour_ganzhi


def test_hour_stem_advances_with_branch() -> None:
    # 甲子日: 子=甲子, 丑=乙丑, 寅=丙寅 … 時支が進むと時干も1ずつ進む。
    base = dt.datetime(2000, 1, 7, 0, 30)   # 子 → 甲子
    assert get_hour_pillar(base).ganzhi_name == "甲子"
    assert get_hour_pillar(base.replace(hour=1)).ganzhi_name == "乙丑"
    assert get_hour_pillar(base.replace(hour=3)).ganzhi_name == "丙寅"
    assert get_hour_pillar(base.replace(hour=11)).ganzhi_name == "庚午"


# ---------------------------------------------------------------------------
# 3. 子刻（論点A: 23時で翌日）
# ---------------------------------------------------------------------------

def test_late_night_shifts_day_for_hour_stem() -> None:
    # 2000-01-07 23:30。23時以降＝翌日(1/8=乙丑日, 日干乙)の子時。
    # 乙日 → 丙子（五鼠遁）。
    late = dt.datetime(2000, 1, 7, 23, 30)
    assert get_hour_pillar(late, late_night_boundary=True).ganzhi_name == "丙子"
    # 論点C（暦日基準）なら当日(甲日)の子時＝甲子
    assert get_hour_pillar(late, late_night_boundary=False).ganzhi_name == "甲子"


def test_hour_day_stem_consistent_with_day_pillar() -> None:
    """時柱の日干（五鼠遁の元）は、同じ境界規則の日柱と一致する。"""
    late = dt.datetime(2000, 1, 7, 23, 30)
    fp = get_four_pillars(late, late_night_boundary=True)
    # 日柱は翌日(乙丑)、時柱は丙子で整合
    assert fp.day.ganzhi_name == "乙丑"
    assert fp.hour.ganzhi_name == "丙子"


# ---------------------------------------------------------------------------
# 4. 四柱
# ---------------------------------------------------------------------------

def test_four_pillars_with_time() -> None:
    fp = get_four_pillars(dt.datetime(2000, 1, 7, 10, 0))
    assert fp.hour is not None
    assert fp.hour.ganzhi_name == "己巳"  # 甲日の巳時
    assert fp.hour.time_range == "09:00-11:00"


def test_four_pillars_without_time_has_no_hour() -> None:
    fp = get_four_pillars(dt.date(2000, 1, 7))
    assert fp.hour is None


def test_four_pillars_json_serializable() -> None:
    import json
    json.dumps(get_four_pillars(dt.datetime(1990, 4, 15, 14, 20)).to_dict(), ensure_ascii=False)
    json.dumps(get_four_pillars(dt.date(1990, 4, 15)).to_dict(), ensure_ascii=False)


# ---------------------------------------------------------------------------
# 5. 四柱バランス（論点C）
# ---------------------------------------------------------------------------

def test_balance_uses_four_pillars_when_time_given() -> None:
    with_time = get_five_element_balance(dt.datetime(2000, 1, 7, 10, 0))
    date_only = get_five_element_balance(dt.date(2000, 1, 7))
    assert with_time.pillar_count == 4
    assert date_only.pillar_count == 3
    # 時柱ぶんスコアが増える
    assert with_time.total > date_only.total


def test_balance_hour_can_be_disabled() -> None:
    b = get_five_element_balance(dt.datetime(2000, 1, 7, 10, 0), include_hour=False)
    assert b.pillar_count == 3


def test_balance_percentages_sum_100_with_hour() -> None:
    b = get_five_element_balance(dt.datetime(1990, 4, 15, 14, 20))
    assert sum(b.percentages.values()) == 100
    assert sum(b.scores.values()) == b.total

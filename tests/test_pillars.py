"""Phase 2（年柱・月柱・節入り）のユニットテスト。"""

from __future__ import annotations

import datetime as dt

import pytest

from app.engine import (
    STEMS,
    find_solar_term,
    get_year_pillar,
    get_month_pillar,
    get_three_pillars,
    get_day_pillar,
)
from app.engine.solar import JST


# ---------------------------------------------------------------------------
# 1. 節気（節入り）の算出 — 国立天文台の暦要項に対し「日」が一致すること
#    （本エンジンの精度は約 ±数分。日単位では一致する）
# ---------------------------------------------------------------------------

KNOWN_RISSHUN = {  # 立春（太陽黄経 315°）の年 → 期待する月日
    1985: (2, 4),
    2000: (2, 4),
    2020: (2, 4),
    2021: (2, 3),  # 124年ぶりの 2/3 立春
    2024: (2, 4),
    2025: (2, 3),
}


@pytest.mark.parametrize("year, md", KNOWN_RISSHUN.items())
def test_risshun_day_matches_almanac(year: int, md: tuple[int, int]) -> None:
    t = find_solar_term(year, 315.0)
    assert t.tzinfo is JST
    assert (t.month, t.day) == md


def test_other_solar_terms_day_matches() -> None:
    # 春分(0°)・夏至(90°)・冬至(270°) の日付（暦要項）
    assert (find_solar_term(2024, 0.0).month, find_solar_term(2024, 0.0).day) == (3, 20)
    assert (find_solar_term(2024, 90.0).month, find_solar_term(2024, 90.0).day) == (6, 21)
    assert (find_solar_term(2023, 270.0).month, find_solar_term(2023, 270.0).day) == (12, 22)


# ---------------------------------------------------------------------------
# 2. 年柱（立春基準）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "date, expected",
    [
        (dt.date(1984, 6, 1), "甲子"),   # 干支紀年の基準
        (dt.date(2024, 6, 1), "甲辰"),
        (dt.date(2000, 6, 1), "庚辰"),
        (dt.date(1999, 6, 1), "己卯"),
    ],
)
def test_year_pillar_midyear(date: dt.date, expected: str) -> None:
    assert get_year_pillar(date).ganzhi_name == expected


def test_year_before_risshun_uses_previous_year() -> None:
    # 2000-01-15 は立春前 → 前年 1999 = 己卯
    yp = get_year_pillar(dt.date(2000, 1, 15))
    assert yp.astrological_year == 1999
    assert yp.ganzhi_name == "己卯"


def test_year_pillar_flips_across_risshun_same_day() -> None:
    """2024 立春は 2/4 17時台。同じ 2/4 でも正午は前年・夜は当年。"""
    noon = get_year_pillar(dt.datetime(2024, 2, 4, 12, 0))   # 立春前
    night = get_year_pillar(dt.datetime(2024, 2, 4, 20, 0))  # 立春後
    assert noon.ganzhi_name == "癸卯"
    assert night.ganzhi_name == "甲辰"


def test_year_pillar_2021_risshun_feb3() -> None:
    assert get_year_pillar(dt.datetime(2021, 2, 3, 12, 0)).ganzhi_name == "庚子"  # 立春前
    assert get_year_pillar(dt.datetime(2021, 2, 4, 12, 0)).ganzhi_name == "辛丑"  # 立春後


# ---------------------------------------------------------------------------
# 3. 月柱（節入り基準 + 五虎遁）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "date, expected_year, expected_month, expected_term",
    [
        # 甲辰年の寅月＝丙寅（甲己之年丙作首）
        (dt.date(2024, 2, 10), "甲辰", "丙寅", "立春"),
        # 甲辰年の卯月＝丁卯（啓蟄後）
        (dt.date(2024, 3, 10), "甲辰", "丁卯", "啓蟄"),
        # 庚辰年の未月＝癸未（乙庚之年戊為頭 → 戊寅…癸未）
        (dt.date(2000, 7, 20), "庚辰", "癸未", "小暑"),
    ],
)
def test_month_pillar_known(date, expected_year, expected_month, expected_term) -> None:
    yp = get_year_pillar(date)
    mp = get_month_pillar(date)
    assert yp.ganzhi_name == expected_year
    assert mp.ganzhi_name == expected_month
    assert mp.solar_term_name == expected_term


def test_month_and_year_flip_across_risshun_same_day() -> None:
    """立春当日をまたぐと、年柱・月柱がともに切り替わる（2024-02-04）。"""
    noon = get_three_pillars(dt.datetime(2024, 2, 4, 12, 0))   # 立春前
    night = get_three_pillars(dt.datetime(2024, 2, 4, 20, 0))  # 立春後
    assert (noon.year.ganzhi_name, noon.month.ganzhi_name) == ("癸卯", "乙丑")
    assert (night.year.ganzhi_name, night.month.ganzhi_name) == ("甲辰", "丙寅")
    # 日柱は暦日基準なので同一
    assert noon.day.ganzhi_name == night.day.ganzhi_name


def test_month_stem_follows_five_tiger_rule() -> None:
    """五虎遁: 寅月の天干 = ((年干%5)*2+2)%10 を全年干で検証。"""
    # 各年干を持つ年の「寅月」(立春直後)を代表日で確認する。
    # 立春〜啓蟄の間（2月中旬）は必ず寅月。
    expected_tiger = {  # 年干名 -> 寅月の天干名
        "甲": "丙", "己": "丙",
        "乙": "戊", "庚": "戊",
        "丙": "庚", "辛": "庚",
        "丁": "壬", "壬": "壬",
        "戊": "甲", "癸": "甲",
    }
    for year in range(2014, 2024):  # 10年分＝10種の年干を網羅
        d = dt.date(year, 2, 20)  # 寅月の代表日
        yp = get_year_pillar(d)
        mp = get_month_pillar(d)
        assert mp.month_branch_name == "寅"
        assert mp.month_stem_name == expected_tiger[yp.year_stem_name]


def test_all_twelve_months_within_one_astro_year() -> None:
    """1年をたどると 12 の月支が寅→丑まで一巡し、干支が連続する。"""
    # 2024 立春〜2025 立春 の各月の代表日（各節の約1週間後）。
    reps = [
        dt.date(2024, 2, 10),  # 寅
        dt.date(2024, 3, 15),  # 卯
        dt.date(2024, 4, 15),  # 辰
        dt.date(2024, 5, 15),  # 巳
        dt.date(2024, 6, 15),  # 午
        dt.date(2024, 7, 15),  # 未
        dt.date(2024, 8, 15),  # 申
        dt.date(2024, 9, 15),  # 酉
        dt.date(2024, 10, 15), # 戌
        dt.date(2024, 11, 15), # 亥
        dt.date(2024, 12, 15), # 子
        dt.date(2025, 1, 15),  # 丑
    ]
    branches = [get_month_pillar(d).month_branch_name for d in reps]
    assert branches == ["寅", "卯", "辰", "巳", "午", "未",
                        "申", "酉", "戌", "亥", "子", "丑"]
    # 月干支が 1 ずつ連続することを確認
    stems = [get_month_pillar(d).month_stem_index for d in reps]
    for i in range(1, 12):
        assert stems[i] == (stems[0] + i) % 10


# ---------------------------------------------------------------------------
# 4. 三柱まとめ・整合性・JSON
# ---------------------------------------------------------------------------

def test_three_pillars_day_matches_phase1() -> None:
    d = dt.date(1990, 4, 15)
    tp = get_three_pillars(d)
    assert tp.day.ganzhi_name == get_day_pillar(d).ganzhi_name


def test_three_pillars_json_serializable() -> None:
    import json
    tp = get_three_pillars(dt.datetime(1995, 8, 20, 9, 30))
    json.dumps(tp.to_dict(), ensure_ascii=False)


def test_pillar_element_yinyang_consistency() -> None:
    """年柱・月柱の五行/陰陽が天干 index と整合する。"""
    yp = get_year_pillar(dt.date(2024, 6, 1))  # 甲辰 → 木/陽
    assert (yp.五行, yp.陰陽) == ("木", "陽")
    mp = get_month_pillar(dt.date(2024, 2, 10))  # 丙寅 → 火/陽
    assert (mp.五行, mp.陰陽) == ("火", "陽")


def test_date_input_assumes_noon_but_not_midnight_off_by_one() -> None:
    """date 入力は正午仮定。立春当日でも正午なら安定して判定できる。"""
    # 2024-02-05 は立春(2/4)の翌日 → 必ず甲辰・寅月
    tp = get_three_pillars(dt.date(2024, 2, 5))
    assert tp.year.ganzhi_name == "甲辰"
    assert tp.month.month_branch_name == "寅"

"""真太陽時補正（経度＋均時差）のユニットテスト。"""

from __future__ import annotations

import datetime as dt

import pytest

from app.engine import (
    equation_of_time_minutes,
    to_true_solar_time,
    get_hour_pillar,
    get_four_pillars,
    CITY_LONGITUDE,
)
from app.engine.solar import datetime_to_jd, JST


def _eot(y: int, m: int, d: int) -> float:
    return equation_of_time_minutes(datetime_to_jd(dt.datetime(y, m, d, 12, 0, tzinfo=JST)))


# ---------------------------------------------------------------------------
# 1. 均時差（暦要項レベルの既知値と符号・概値が一致）
# ---------------------------------------------------------------------------

def test_equation_of_time_known_values() -> None:
    assert _eot(2024, 2, 12) == pytest.approx(-14.2, abs=0.6)   # 2月中旬は負
    assert _eot(2024, 11, 3) == pytest.approx(16.4, abs=0.6)    # 11月上旬は正の極大付近
    assert abs(_eot(2024, 4, 15)) < 1.5                          # 4月中旬はゼロ付近
    assert abs(_eot(2024, 9, 1)) < 1.5                           # 9月初旬はゼロ付近


# ---------------------------------------------------------------------------
# 2. 経度補正
# ---------------------------------------------------------------------------

def test_longitude_shift_east_is_positive() -> None:
    # 東京(139.69°)は 135°より東 → 約 +18.8 分（均時差OFFで検証）
    base = dt.datetime(2024, 6, 1, 12, 0, tzinfo=JST)
    corrected = to_true_solar_time(base, 139.69, apply_equation_of_time=False)
    delta_min = (corrected - base).total_seconds() / 60.0
    assert delta_min == pytest.approx((139.69 - 135.0) * 4.0, abs=0.01)
    assert delta_min > 0


def test_standard_meridian_no_shift_without_eot() -> None:
    base = dt.datetime(2024, 6, 1, 10, 30, tzinfo=JST)
    corrected = to_true_solar_time(base, 135.0, apply_equation_of_time=False)
    assert corrected == base


# ---------------------------------------------------------------------------
# 3. 時柱への反映（境界をまたぐ）
# ---------------------------------------------------------------------------

def test_longitude_can_shift_hour_branch() -> None:
    # 10:50 JST は巳時。東京経度(+18.8分)で 11:08 → 午時に変わる（均時差OFF）。
    v = dt.datetime(2000, 1, 7, 10, 50)
    assert get_hour_pillar(v).hour_branch_name == "巳"  # 補正なし
    shifted = get_hour_pillar(v, longitude=139.69)
    assert shifted.hour_branch_name == "午"


def test_no_correction_matches_plain() -> None:
    v = dt.datetime(2000, 1, 7, 14, 20)
    assert (
        get_hour_pillar(v).ganzhi_name
        == get_hour_pillar(v, longitude=135.0, apply_equation_of_time=False).ganzhi_name
    )


def test_eot_only_correction_applies() -> None:
    # 2月中旬(EoT≈-14分)。11:06 JST は午時だが、均時差-14分で 10:52 → 巳時。
    v = dt.datetime(2024, 2, 12, 11, 6)
    assert get_hour_pillar(v).hour_branch_name == "午"
    corrected = get_hour_pillar(v, apply_equation_of_time=True)  # longitude=135
    assert corrected.hour_branch_name == "巳"


# ---------------------------------------------------------------------------
# 4. 四柱での整合（補正後、日柱の日干＝時柱の日干）
# ---------------------------------------------------------------------------

def test_four_pillars_correction_keeps_day_hour_consistent() -> None:
    # 23:10 JST・西の経度(福岡130.4°→約-18.4分)で 22:52 → 前日扱いにならない子刻境界の確認
    v = dt.datetime(2000, 1, 7, 23, 10)
    fp_plain = get_four_pillars(v)  # 23時台 → 翌日(乙丑)・丙子
    fp_west = get_four_pillars(v, longitude=CITY_LONGITUDE["福岡"])  # -18分で22:52 → 当日(甲子)・亥時
    assert fp_plain.day.ganzhi_name == "乙丑"
    assert fp_plain.hour.hour_branch_name == "子"
    # 福岡補正で 22:52 → 亥時、日柱は当日(甲子)のまま
    assert fp_west.hour.hour_branch_name == "亥"
    assert fp_west.day.ganzhi_name == "甲子"


def test_city_longitude_table() -> None:
    assert set(["東京", "大阪", "福岡", "那覇"]).issubset(CITY_LONGITUDE.keys())
    assert CITY_LONGITUDE["東京"] == pytest.approx(139.69, abs=0.5)

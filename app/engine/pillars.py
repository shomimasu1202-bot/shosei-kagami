"""年柱・月柱の算出（立春・節入りの処理を含む）。

== 年柱（年干支）==
四柱推命の年は元日でも旧正月でもなく、**立春（太陽黄経 315°）**で切り替わる。
立春より前は前年の干支を用いる。
    年干 index = (立春基準の年 − 4) mod 10   （西暦4年 = 甲子）
    年支 index = (立春基準の年 − 4) mod 12
検算: 1984 = 甲子、2024 = 甲辰、2000 = 庚辰。

== 月柱（月干支）==
月は 12 の「節」（立春・啓蟄・清明…）で切り替わる。月支は立春から始まる寅月を
先頭に固定される（寅→丑）。月支は生誕時の太陽黄経から直接決まる:
    k（月の順序, 0=寅） = floor(((L − 315) mod 360) / 30)
    月支 index = (k + 2) mod 12      （寅 = index 2）

月干は「五虎遁（年上起月）」で年干から決まる:
    寅月の天干 = ((年干 index mod 5) * 2 + 2) mod 10
    月干 index = (寅月の天干 + k) mod 10
検算: 甲/己年の寅月=丙寅、乙/庚年=戊寅、丙/辛年=庚寅、丁/壬年=壬寅、戊/癸年=甲寅。
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, asdict

from .ganzhi import STEMS, BRANCHES, DayPillar, get_day_pillar
from .five_elements import element_of_stem, yinyang_of_stem, element_of_branch
from .solar import (
    JST,
    SOLAR_TERM_NAMES,
    SOLAR_TERM_LONGITUDES,
    solar_longitude,
    find_solar_term,
    datetime_to_jd,
    normalize_to_jst,
)

# 西暦4年 = 甲子（干支紀年法の基準）。
_YEAR_GANZHI_OFFSET = 4


@dataclass(frozen=True)
class YearPillar:
    """年柱（年干支）。JSON シリアライズ可能。"""

    year_stem_index: int
    year_branch_index: int
    year_stem_name: str
    year_branch_name: str
    astrological_year: int  # 立春基準の年（暦年と異なる場合がある）
    五行: str
    陰陽: str

    @property
    def ganzhi_name(self) -> str:
        return f"{self.year_stem_name}{self.year_branch_name}"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class MonthPillar:
    """月柱（月干支）。JSON シリアライズ可能。"""

    month_stem_index: int
    month_branch_index: int
    month_stem_name: str
    month_branch_name: str
    month_order: int          # 0=寅月 … 11=丑月
    solar_term_name: str      # この月を始める節（例: 立春）
    五行: str                  # 月干の五行
    陰陽: str                  # 月干の陰陽

    @property
    def ganzhi_name(self) -> str:
        return f"{self.month_stem_name}{self.month_branch_name}"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ThreePillars:
    """三柱（年柱・月柱・日柱）。時柱は Phase 3 で追加予定。"""

    year: YearPillar
    month: MonthPillar
    day: DayPillar

    def to_dict(self) -> dict:
        return {
            "year": self.year.to_dict(),
            "month": self.month.to_dict(),
            "day": self.day.to_dict(),
        }


def _astrological_year(jd_ut: float, calendar_year: int) -> int:
    """立春を基準にした年を返す。立春より前なら暦年 − 1。"""
    risshun = find_solar_term(calendar_year, 315.0)  # JST
    risshun_jd = datetime_to_jd(risshun)
    return calendar_year if jd_ut >= risshun_jd else calendar_year - 1


def get_year_pillar(
    value: _dt.date | _dt.datetime,
    *,
    assumed_hour: int = 12,
) -> YearPillar:
    """生年月日（＋時刻）→ 年柱。立春で年を切り替える。"""
    jst_dt = normalize_to_jst(value, assumed_hour=assumed_hour)
    jd = datetime_to_jd(jst_dt)
    astro_year = _astrological_year(jd, jst_dt.year)

    stem_index = (astro_year - _YEAR_GANZHI_OFFSET) % 10
    branch_index = (astro_year - _YEAR_GANZHI_OFFSET) % 12
    return YearPillar(
        year_stem_index=stem_index,
        year_branch_index=branch_index,
        year_stem_name=STEMS[stem_index],
        year_branch_name=BRANCHES[branch_index],
        astrological_year=astro_year,
        五行=element_of_stem(stem_index),
        陰陽=yinyang_of_stem(stem_index),
    )


def get_month_pillar(
    value: _dt.date | _dt.datetime,
    *,
    assumed_hour: int = 12,
) -> MonthPillar:
    """生年月日（＋時刻）→ 月柱。節入りで月を切り替える。"""
    jst_dt = normalize_to_jst(value, assumed_hour=assumed_hour)
    jd = datetime_to_jd(jst_dt)

    # 月支: 太陽黄経から直接。寅月(315°)を先頭に 30° 区切り。
    lon = solar_longitude(jd)
    k = int(((lon - 315.0) % 360.0) // 30.0)  # 0=寅 … 11=丑
    branch_index = (k + 2) % 12

    # 月干: 五虎遁（年干から）。年は立春基準。
    astro_year = _astrological_year(jd, jst_dt.year)
    year_stem_index = (astro_year - _YEAR_GANZHI_OFFSET) % 10
    tiger_month_stem = ((year_stem_index % 5) * 2 + 2) % 10
    stem_index = (tiger_month_stem + k) % 10

    return MonthPillar(
        month_stem_index=stem_index,
        month_branch_index=branch_index,
        month_stem_name=STEMS[stem_index],
        month_branch_name=BRANCHES[branch_index],
        month_order=k,
        solar_term_name=SOLAR_TERM_NAMES[k],
        五行=element_of_stem(stem_index),
        陰陽=yinyang_of_stem(stem_index),
    )


def get_month_solar_term_start(
    value: _dt.date | _dt.datetime,
    *,
    assumed_hour: int = 12,
) -> _dt.datetime:
    """生誕日が属する月（節月）を始めた「節入り」の JST 日時を返す。

    月律分野蔵干の司令判定に使う「節入りからの経過日数」の起点。
    """
    jst_dt = normalize_to_jst(value, assumed_hour=assumed_hour)
    jd = datetime_to_jd(jst_dt)
    lon = solar_longitude(jd)
    k = int(((lon - 315.0) % 360.0) // 30.0)  # 0=寅 … 11=丑
    target = SOLAR_TERM_LONGITUDES[k]
    # 生誕以前で最も近い当該節の occurrence を選ぶ（年境をまたぐ節に対応）。
    candidates = [
        find_solar_term(y, target) for y in (jst_dt.year - 1, jst_dt.year, jst_dt.year + 1)
    ]
    past = [c for c in candidates if c <= jst_dt]
    return max(past)


def get_three_pillars(
    value: _dt.date | _dt.datetime,
    *,
    assumed_hour: int = 12,
    late_night_boundary: bool = False,
) -> ThreePillars:
    """年柱・月柱・日柱をまとめて返す。

    日柱は Phase 1 の civil date 基準（late_night_boundary オプション対応）。
    年柱・月柱は JST での太陽黄経に基づく（assumed_hour は時刻不明時の仮定）。
    """
    return ThreePillars(
        year=get_year_pillar(value, assumed_hour=assumed_hour),
        month=get_month_pillar(value, assumed_hour=assumed_hour),
        day=get_day_pillar(value, late_night_boundary=late_night_boundary),
    )

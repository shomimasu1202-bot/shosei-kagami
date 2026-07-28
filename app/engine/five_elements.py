"""五行（木火土金水）・陰陽の判定。

十干 → 五行 / 陰陽:
    甲乙=木、丙丁=火、戊己=土、庚辛=金、壬癸=水
    甲丙戊庚壬=陽、乙丁己辛癸=陰

十二支 → 五行（後続フェーズで使用）:
    子亥=水、寅卯=木、巳午=火、申酉=金、辰戌丑未=土
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, asdict

from .ganzhi import STEMS, BRANCHES, get_day_pillar

# 十干 index (0〜9) → 五行。甲乙=木 ... 壬癸=水。
# STEMS の並び順（甲乙丙丁戊己庚辛壬癸）では stem_index // 2 が五行に対応する。
STEM_TO_ELEMENT: dict[int, str] = {
    0: "木", 1: "木",   # 甲 乙
    2: "火", 3: "火",   # 丙 丁
    4: "土", 5: "土",   # 戊 己
    6: "金", 7: "金",   # 庚 辛
    8: "水", 9: "水",   # 壬 癸
}

# 十干 index (0〜9) → 陰陽。偶数 index（甲丙戊庚壬）=陽、奇数（乙丁己辛癸）=陰。
STEM_TO_YINYANG: dict[int, str] = {
    i: ("陽" if i % 2 == 0 else "陰") for i in range(10)
}

# 十二支 index (0〜11) → 五行。子(0)丑(1)寅(2)卯(3)辰(4)巳(5)午(6)未(7)申(8)酉(9)戌(10)亥(11)
BRANCH_TO_ELEMENT: dict[int, str] = {
    0: "水",   # 子
    1: "土",   # 丑
    2: "木",   # 寅
    3: "木",   # 卯
    4: "土",   # 辰
    5: "火",   # 巳
    6: "火",   # 午
    7: "土",   # 未
    8: "金",   # 申
    9: "金",   # 酉
    10: "土",  # 戌
    11: "水",  # 亥
}


@dataclass(frozen=True)
class FiveElementProfile:
    """日干の五行・陰陽プロファイル。JSON シリアライズ可能。"""

    五行: str  # 木 / 火 / 土 / 金 / 水
    陰陽: str  # 陽 / 陰

    def to_dict(self) -> dict:
        return asdict(self)


def element_of_stem(stem_index: int) -> str:
    """十干 index → 五行。"""
    return STEM_TO_ELEMENT[stem_index]


def yinyang_of_stem(stem_index: int) -> str:
    """十干 index → 陰陽。"""
    return STEM_TO_YINYANG[stem_index]


def element_of_branch(branch_index: int) -> str:
    """十二支 index → 五行（後続フェーズ用）。"""
    return BRANCH_TO_ELEMENT[branch_index]


def get_five_element_profile(
    value: _dt.date | _dt.datetime,
    *,
    late_night_boundary: bool = False,
) -> FiveElementProfile:
    """生年月日 → 日干の五行・陰陽プロファイル。"""
    pillar = get_day_pillar(value, late_night_boundary=late_night_boundary)
    return FiveElementProfile(
        五行=element_of_stem(pillar.day_stem_index),
        陰陽=yinyang_of_stem(pillar.day_stem_index),
    )

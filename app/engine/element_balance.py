"""三柱（年・月・日）の五行バランス算出（Phase 2.7）。

年柱・月柱・日柱の「天干＋地支」計6要素の五行を集計し、
どの五行が強く（多く）、どの五行が控えめ（少ない・欠けている）かを求める。
これを鑑定文の味付けに反映することで、同じ日干（タイプ）でも生年月日全体で
内容が変わり、個別化が深まる。

※ 本フェーズは天干・地支の本気（表の五行）のみを数える簡易版。
  蔵干（地支に隠れた天干）の重み付けは後続フェーズの拡張余地とする。
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

from .five_elements import element_of_stem, element_of_branch
from .pillars import get_three_pillars

# 集計・表示順（相生順）。
ELEMENTS_ORDER: tuple[str, ...] = ("木", "火", "土", "金", "水")

# 強い五行が示す持ち味。
_STRONG_TRAIT: dict[str, str] = {
    "木": "伸びやかな成長力と向上心",
    "火": "明るい情熱と表現力",
    "土": "どっしりした安定感と信頼感",
    "金": "けじめのある誠実さと美意識",
    "水": "しなやかな感受性と知性",
}

# 控えめ・欠けている五行について、意識して補うとよい面。
_LACK_TRAIT: dict[str, str] = {
    "木": "新しく一歩踏み出す柔軟さ",
    "火": "自分を表に出す華やぎ",
    "土": "腰を据えて続ける安定",
    "金": "物事を整える割り切り",
    "水": "人と潤い合う柔らかさ",
}


@dataclass(frozen=True)
class FiveElementBalance:
    """三柱の五行バランス。JSON シリアライズ可能。"""

    counts: dict[str, int]      # 五行 -> 個数（合計6）
    total: int                  # 6（天干3＋地支3）
    dominant: tuple[str, ...]   # 最多の五行（同数なら複数）
    lacking: tuple[str, ...]    # 個数0の五行（無ければ空）
    day_master: str             # 日干の五行（本人＝日主）
    comment: str                # 一言サマリ

    def to_dict(self) -> dict:
        return {
            "counts": dict(self.counts),
            "total": self.total,
            "dominant": list(self.dominant),
            "lacking": list(self.lacking),
            "day_master": self.day_master,
            "comment": self.comment,
        }


def _make_comment(dominant: tuple[str, ...], lacking: tuple[str, ...]) -> str:
    dom = "・".join(dominant)
    if lacking:
        return f"{dom}が強め、{'・'.join(lacking)}が控えめ"
    return f"{dom}が強め、五行のバランス良好"


def get_five_element_balance(
    value: _dt.date | _dt.datetime,
    *,
    assumed_hour: int = 12,
    late_night_boundary: bool = False,
) -> FiveElementBalance:
    """生年月日（＋時刻）→ 三柱の五行バランス。"""
    tp = get_three_pillars(
        value, assumed_hour=assumed_hour, late_night_boundary=late_night_boundary
    )
    counts = {e: 0 for e in ELEMENTS_ORDER}

    for stem_index in (
        tp.year.year_stem_index,
        tp.month.month_stem_index,
        tp.day.day_stem_index,
    ):
        counts[element_of_stem(stem_index)] += 1
    for branch_index in (
        tp.year.year_branch_index,
        tp.month.month_branch_index,
        tp.day.day_branch_index,
    ):
        counts[element_of_branch(branch_index)] += 1

    total = sum(counts.values())
    mx = max(counts.values())
    dominant = tuple(e for e in ELEMENTS_ORDER if counts[e] == mx)
    lacking = tuple(e for e in ELEMENTS_ORDER if counts[e] == 0)
    day_master = element_of_stem(tp.day.day_stem_index)

    return FiveElementBalance(
        counts=counts,
        total=total,
        dominant=dominant,
        lacking=lacking,
        day_master=day_master,
        comment=_make_comment(dominant, lacking),
    )


def describe_balance(balance: FiveElementBalance) -> str:
    """五行バランスを敬体の段落文にする（鑑定文の「五行バランス」セクション用）。"""
    counts_str = "・".join(f"{e}{balance.counts[e]}" for e in ELEMENTS_ORDER)
    dom = "と".join(balance.dominant)
    strong = "、".join(_STRONG_TRAIT[e] for e in balance.dominant)

    s1 = f"あなたの三柱（年・月・日）には、{counts_str}の割合で五行の気が巡っています。"
    s2 = f"中でも{dom}の気が豊かで、{strong}があなたの持ち味をいっそう強めています。"

    if balance.lacking:
        lack = "と".join(balance.lacking)
        weak = "、".join(_LACK_TRAIT[e] for e in balance.lacking)
        s3 = f"いっぽう{lack}の気は控えめなので、{weak}を少し意識すると、いっそう伸びやかになれます。"
    else:
        s3 = "五行がまんべんなく巡っており、さまざまな面を器用に活かしていけるでしょう。"

    return s1 + s2 + s3

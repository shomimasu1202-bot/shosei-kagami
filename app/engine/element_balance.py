"""三柱（年・月・日）の五行バランス算出（Phase 2.7 / 蔵干対応で本格化）。

年柱・月柱・日柱の「天干」と「地支の蔵干」の五行を重み付きで集計し、
どの五行が強く、どの五行が控えめ（欠けている）かを求める。
これを鑑定文の味付けに反映し、同じ日干でも生年月日全体で内容が変わる。

== 集計モデル ==
    天干（年・月・日の3つ）      : 各 STEM_WEIGHT
    地支の蔵干（本気/中気/余気） : 本気=HONKI_WEIGHT, 中気=CHUKI_WEIGHT, 余気=YOKI_WEIGHT
    include_hidden_stems=False のときは「可視のみ」（天干＝1、地支は本気＝1のみ、
    中気・余気は 0）となり、旧来の整数カウント（合計6）を再現する。

蔵干テーブルの出典は hidden_stems.py 参照。月律分野（節入りからの経過日数で
本気/中気/余気の比率を変える）は後続の拡張余地。
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

from .five_elements import element_of_stem
from .hidden_stems import hidden_stems_of_branch, HONKI, CHUKI, YOKI
from .pillars import get_three_pillars

# 集計・表示順（相生順）。
ELEMENTS_ORDER: tuple[str, ...] = ("木", "火", "土", "金", "水")

# 重み（本格：蔵干あり）。定数として調整可能。
STEM_WEIGHT = 3
HONKI_WEIGHT = 3
CHUKI_WEIGHT = 2
YOKI_WEIGHT = 1

_ROLE_WEIGHT = {HONKI: HONKI_WEIGHT, CHUKI: CHUKI_WEIGHT, YOKI: YOKI_WEIGHT}
# 可視のみ（蔵干なし）: 天干1、本気1、中気・余気0 → 旧来の合計6カウント。
_ROLE_WEIGHT_VISIBLE = {HONKI: 1, CHUKI: 0, YOKI: 0}

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

    scores: dict[str, int]         # 五行 -> 重み付きスコア
    total: int                     # スコア合計
    percentages: dict[str, int]    # 五行 -> 百分率（合計100）
    dominant: tuple[str, ...]      # 最大スコアの五行（同点なら複数）
    lacking: tuple[str, ...]       # スコア0の五行（無ければ空）
    day_master: str                # 日干の五行（本人＝日主）
    include_hidden_stems: bool     # 蔵干を含めたか
    comment: str                   # 一言サマリ

    def to_dict(self) -> dict:
        return {
            "scores": dict(self.scores),
            "total": self.total,
            "percentages": dict(self.percentages),
            "dominant": list(self.dominant),
            "lacking": list(self.lacking),
            "day_master": self.day_master,
            "include_hidden_stems": self.include_hidden_stems,
            "comment": self.comment,
        }


def _to_percentages(scores: dict[str, int], total: int) -> dict[str, int]:
    """スコア → 百分率（合計がちょうど100になるよう最大剰余法で丸める）。"""
    if total <= 0:
        return {e: 0 for e in ELEMENTS_ORDER}
    exact = {e: scores[e] * 100 / total for e in ELEMENTS_ORDER}
    floored = {e: int(exact[e]) for e in ELEMENTS_ORDER}
    remainder = 100 - sum(floored.values())
    # 小数部が大きい順に +1 して合計100に合わせる。
    order = sorted(ELEMENTS_ORDER, key=lambda e: exact[e] - floored[e], reverse=True)
    for e in order[:remainder]:
        floored[e] += 1
    return floored


def _make_comment(dominant: tuple[str, ...], lacking: tuple[str, ...]) -> str:
    dom = "・".join(dominant)
    if lacking:
        return f"{dom}が強め、{'・'.join(lacking)}が控えめ"
    return f"{dom}が強め、五行のバランス良好"


def get_five_element_balance(
    value: _dt.date | _dt.datetime,
    *,
    include_hidden_stems: bool = True,
    assumed_hour: int = 12,
    late_night_boundary: bool = False,
) -> FiveElementBalance:
    """生年月日（＋時刻）→ 三柱の五行バランス。

    include_hidden_stems=True（既定）は蔵干を含む本格版。
    False は可視のみ（天干＋地支本気、各1、合計6）の簡易版。
    """
    tp = get_three_pillars(
        value, assumed_hour=assumed_hour, late_night_boundary=late_night_boundary
    )
    role_weight = _ROLE_WEIGHT if include_hidden_stems else _ROLE_WEIGHT_VISIBLE
    stem_weight = STEM_WEIGHT if include_hidden_stems else 1

    scores = {e: 0 for e in ELEMENTS_ORDER}

    # 天干（年・月・日）
    for stem_index in (
        tp.year.year_stem_index,
        tp.month.month_stem_index,
        tp.day.day_stem_index,
    ):
        scores[element_of_stem(stem_index)] += stem_weight

    # 地支の蔵干（年・月・日）
    for branch_index in (
        tp.year.year_branch_index,
        tp.month.month_branch_index,
        tp.day.day_branch_index,
    ):
        for hidden_stem_index, role in hidden_stems_of_branch(branch_index):
            scores[element_of_stem(hidden_stem_index)] += role_weight[role]

    total = sum(scores.values())
    mx = max(scores.values())
    dominant = tuple(e for e in ELEMENTS_ORDER if scores[e] == mx)
    lacking = tuple(e for e in ELEMENTS_ORDER if scores[e] == 0)
    day_master = element_of_stem(tp.day.day_stem_index)

    return FiveElementBalance(
        scores=scores,
        total=total,
        percentages=_to_percentages(scores, total),
        dominant=dominant,
        lacking=lacking,
        day_master=day_master,
        include_hidden_stems=include_hidden_stems,
        comment=_make_comment(dominant, lacking),
    )


def describe_balance(balance: FiveElementBalance) -> str:
    """五行バランスを敬体の段落文にする（鑑定文の「五行バランス」セクション用）。"""
    pct = balance.percentages
    pct_str = "・".join(f"{e}{pct[e]}%" for e in ELEMENTS_ORDER)
    dom = "と".join(balance.dominant)
    strong = "、".join(_STRONG_TRAIT[e] for e in balance.dominant)

    kura = "（地支の蔵干を含めて）" if balance.include_hidden_stems else ""
    s1 = f"あなたの三柱（年・月・日）を{kura}五行で見ると、{pct_str}の巡りです。"
    s2 = f"中でも{dom}の気が豊かで、{strong}があなたの持ち味をいっそう強めています。"

    if balance.lacking:
        lack = "と".join(balance.lacking)
        weak = "、".join(_LACK_TRAIT[e] for e in balance.lacking)
        s3 = f"いっぽう{lack}の気は巡っておらず、{weak}を少し意識すると、いっそう伸びやかになれます。"
    else:
        s3 = "五行がまんべんなく巡っており、さまざまな面を器用に活かしていけるでしょう。"

    return s1 + s2 + s3

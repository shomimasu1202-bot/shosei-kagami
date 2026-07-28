"""相性の算出（Phase 2.6）。

公有である五行の相生・相剋を土台に、日干10タイプ同士の相性を決定的に算出する。
外部AIは使わない。既存ブランドの相性表現は不使用。

== 五行の関係 ==
五行の並び: 木(0) 火(1) 土(2) 金(3) 水(4)
  相生（生む）: 木→火→土→金→水→木        … generates(e) = (e+1) % 5
  相剋（抑える）: 木→土→水→火→金→木        … controls(e)  = (e+2) % 5

A から見た B との関係は次の5通りのいずれか（必ず1つに定まる）:
  - 比和   : 同じ五行（対等・似た者同士）           level ○
  - 相生(A→B): A が B を生む（あなたが活かす）        level ◎
  - 相生(B→A): B が A を生む（相手があなたを活かす）  level ◎
  - 相剋(A→B): A が B を剋する（あなたが動かす）      level △
  - 相剋(B→A): B が A を剋する（相手が引き締める）    level △

陰陽が異なると補い合い、同じだと共感しやすい、というニュアンスを添える。
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, asdict

from .type_table import ShoseiType, TYPE_TABLE, get_type

# 五行の並び（相生順）。相生 = (i+1)%5、相剋 = (i+2)%5。
ELEMENTS: tuple[str, ...] = ("木", "火", "土", "金", "水")
_ELEMENT_INDEX: dict[str, int] = {e: i for i, e in enumerate(ELEMENTS)}


@dataclass(frozen=True)
class Compatibility:
    """2タイプ間の相性（A から見た関係）。JSON シリアライズ可能。"""

    type_id_a: str
    名称_a: str
    type_id_b: str
    名称_b: str
    relation: str    # 比和 / 相生 / 相剋
    direction: str   # 関係の向き（説明ラベル）
    level: str       # ◎ / ○ / △
    comment: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CompatibilityGuide:
    """あるタイプから見た、他タイプとの相性ガイド（名称リスト）。"""

    best: tuple[str, ...]     # 相生（◎）の相手タイプ名称
    caution: tuple[str, ...]  # 相剋（△）の相手タイプ名称

    def to_dict(self) -> dict:
        return {"best": list(self.best), "caution": list(self.caution)}


def element_relation(a_element: str, b_element: str) -> tuple[str, str, str]:
    """A の五行から見た B の五行との関係を (relation, direction, level) で返す。"""
    ia = _ELEMENT_INDEX[a_element]
    ib = _ELEMENT_INDEX[b_element]
    if ia == ib:
        return ("比和", "対等", "○")
    if (ia + 1) % 5 == ib:            # A 生 B
        return ("相生", "あなたが相手を活かす", "◎")
    if (ib + 1) % 5 == ia:            # B 生 A
        return ("相生", "相手があなたを活かす", "◎")
    if (ia + 2) % 5 == ib:            # A 剋 B
        return ("相剋", "あなたが相手を動かす", "△")
    return ("相剋", "相手があなたを引き締める", "△")  # B 剋 A


def _yinyang_note(ya: str, yb: str) -> str:
    if ya != yb:
        return "陰陽が異なり、互いの足りないところを補い合えます。"
    return "陰陽が同じで、感じ方やテンポに共感しやすい間柄です。"


def compatibility_between_types(a: ShoseiType, b: ShoseiType) -> Compatibility:
    """2つのタイプの相性を組み立てる（A から見た視点）。決定的。"""
    relation, direction, level = element_relation(a.五行, b.五行)
    ea, eb = a.五行, b.五行

    if relation == "比和":
        base = f"同じ{ea}の気を持つ、似た者同士。感覚が近く、一緒にいて気楽な相手です。"
    elif relation == "相生" and direction == "あなたが相手を活かす":
        base = f"あなたの{ea}が相手の{eb}を育てる相生の関係。自然と支え、頼られる心地よい相手です。"
    elif relation == "相生":
        base = f"相手の{eb}があなたの{ea}を育てる相生の関係。エネルギーや学びをもらえる、成長できる相手です。"
    elif direction == "あなたが相手を動かす":
        base = (f"あなたの{ea}が相手の{eb}を剋する関係。刺激し合えますが、押しすぎると"
                "摩擦になりやすいので、相手のペースを尊重すると良いご縁になります。")
    else:
        base = (f"相手の{eb}があなたの{ea}を剋する関係。主導権を握られやすいものの、"
                "程よい緊張感が成長につながります。")

    comment = base + _yinyang_note(a.陰陽, b.陰陽)
    return Compatibility(
        type_id_a=a.type_id,
        名称_a=a.名称,
        type_id_b=b.type_id,
        名称_b=b.名称,
        relation=relation,
        direction=direction,
        level=level,
        comment=comment,
    )


def compatibility_guide_for_type(t: ShoseiType) -> CompatibilityGuide:
    """あるタイプから見た、10タイプ中の好相性（相生）・要注意（相剋）を列挙する。

    自分自身と、同五行の比和（○）は中立として挙げない。
    """
    best: list[str] = []
    caution: list[str] = []
    for u in TYPE_TABLE:
        if u.type_id == t.type_id:
            continue
        relation, _, _ = element_relation(t.五行, u.五行)
        if relation == "相生":
            best.append(u.名称)
        elif relation == "相剋":
            caution.append(u.名称)
    return CompatibilityGuide(best=tuple(best), caution=tuple(caution))


def get_compatibility(
    date_a: _dt.date | _dt.datetime,
    date_b: _dt.date | _dt.datetime,
    *,
    late_night_boundary: bool = False,
) -> Compatibility:
    """2人の生年月日 → 相性（1人目 A から見た視点）。"""
    a = get_type(date_a, late_night_boundary=late_night_boundary)
    b = get_type(date_b, late_night_boundary=late_night_boundary)
    return compatibility_between_types(a, b)

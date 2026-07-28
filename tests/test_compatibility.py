"""相性の算出（Phase 2.6）のユニットテスト。"""

from __future__ import annotations

import datetime as dt

import pytest

from app.engine import (
    TYPE_TABLE,
    ELEMENTS,
    element_relation,
    compatibility_between_types,
    compatibility_guide_for_type,
    get_compatibility,
    get_type,
)


# ---------------------------------------------------------------------------
# 1. 五行の関係（相生・相剋・比和）
# ---------------------------------------------------------------------------

def test_element_relation_same_is_hiwa() -> None:
    for e in ELEMENTS:
        rel, _, level = element_relation(e, e)
        assert rel == "比和"
        assert level == "○"


def test_element_relation_sheng_cycle() -> None:
    # 相生: 木→火→土→金→水→木（A が B を活かす、◎）
    sheng = [("木", "火"), ("火", "土"), ("土", "金"), ("金", "水"), ("水", "木")]
    for a, b in sheng:
        rel, direction, level = element_relation(a, b)
        assert rel == "相生"
        assert direction == "あなたが相手を活かす"
        assert level == "◎"
        # 逆向きは「相手があなたを活かす」
        rel_r, dir_r, level_r = element_relation(b, a)
        assert rel_r == "相生" and dir_r == "相手があなたを活かす" and level_r == "◎"


def test_element_relation_ke_cycle() -> None:
    # 相剋: 木→土→水→火→金→木（A が B を剋する、△）
    ke = [("木", "土"), ("土", "水"), ("水", "火"), ("火", "金"), ("金", "木")]
    for a, b in ke:
        rel, direction, level = element_relation(a, b)
        assert rel == "相剋"
        assert direction == "あなたが相手を動かす"
        assert level == "△"
        rel_r, dir_r, level_r = element_relation(b, a)
        assert rel_r == "相剋" and dir_r == "相手があなたを引き締める" and level_r == "△"


def test_every_element_pair_has_exactly_one_relation() -> None:
    valid_levels = {"◎", "○", "△"}
    for a in ELEMENTS:
        for b in ELEMENTS:
            rel, direction, level = element_relation(a, b)
            assert rel in {"比和", "相生", "相剋"}
            assert level in valid_levels


# ---------------------------------------------------------------------------
# 2. タイプ間の相性
# ---------------------------------------------------------------------------

def _type(tid: str):
    return next(t for t in TYPE_TABLE if t.type_id == tid)


def test_compatibility_wood_generates_fire() -> None:
    c = compatibility_between_types(_type("you"), _type("asahi"))  # 木→火
    assert c.relation == "相生"
    assert c.level == "◎"
    assert "相生" in c.comment


def test_compatibility_metal_controls_wood() -> None:
    c = compatibility_between_types(_type("rin"), _type("you"))  # 金剋木
    assert c.relation == "相剋"
    assert c.level == "△"


def test_compatibility_same_element_is_hiwa() -> None:
    c = compatibility_between_types(_type("you"), _type("fuji"))  # 木＝木
    assert c.relation == "比和"
    assert c.level == "○"


def test_yinyang_note_included() -> None:
    # 甲(木陽) と 丁(火陰): 相生 + 陰陽異なる
    c = compatibility_between_types(_type("you"), _type("hotaru"))
    assert "補い合えます" in c.comment
    # 甲(木陽) と 丙(火陽): 相生 + 陰陽同じ
    c2 = compatibility_between_types(_type("you"), _type("asahi"))
    assert "共感しやすい" in c2.comment


def test_level_is_symmetric_between_pair() -> None:
    """レベル（◎○△）は向きに依らず同じ。"""
    for a in TYPE_TABLE:
        for b in TYPE_TABLE:
            ab = compatibility_between_types(a, b)
            ba = compatibility_between_types(b, a)
            assert ab.level == ba.level


# ---------------------------------------------------------------------------
# 3. 相性ガイド（1タイプ視点）
# ---------------------------------------------------------------------------

def test_guide_for_wood_type() -> None:
    guide = compatibility_guide_for_type(_type("you"))  # 木
    # 相生: 木生火(旭,蛍) と 水生木(湊,雫)
    assert set(guide.best) == {"旭", "蛍", "湊", "雫"}
    # 相剋: 木剋土(嶺,苑) と 金剋木(鈴,玉)
    assert set(guide.caution) == {"嶺", "苑", "鈴", "玉"}
    # 自分自身と比和(藤)は含まれない
    assert "葉" not in guide.best and "葉" not in guide.caution
    assert "藤" not in guide.best and "藤" not in guide.caution


def test_guide_covers_only_valid_names() -> None:
    names = {t.名称 for t in TYPE_TABLE}
    for t in TYPE_TABLE:
        guide = compatibility_guide_for_type(t)
        assert set(guide.best) <= names
        assert set(guide.caution) <= names
        # best と caution は重複しない
        assert not (set(guide.best) & set(guide.caution))


# ---------------------------------------------------------------------------
# 4. 生年月日からの相性・JSON
# ---------------------------------------------------------------------------

def test_get_compatibility_from_dates() -> None:
    # 2000-01-07=甲(木), 2000-01-11=戊(土) → 木剋土（△）
    c = get_compatibility(dt.date(2000, 1, 7), dt.date(2000, 1, 11))
    assert c.type_id_a == "you"
    assert c.type_id_b == "mine"
    assert c.relation == "相剋"


def test_compatibility_json_serializable() -> None:
    import json
    c = get_compatibility(dt.date(1990, 4, 15), dt.date(1988, 11, 3))
    json.dumps(c.to_dict(), ensure_ascii=False)

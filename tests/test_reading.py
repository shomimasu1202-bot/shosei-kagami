"""鑑定文生成（Phase 2.5）のユニットテスト。"""

from __future__ import annotations

import datetime as dt

import pytest

from app.engine import (
    TYPE_TABLE,
    SECTIONS,
    get_reading,
    build_reading_for_type,
)
from app.engine.reading import TYPE_TEXT, ELEMENT_FLAVOR, YINYANG_FLAVOR

SECTION_IDS = [sid for sid, _ in SECTIONS]


# ---------------------------------------------------------------------------
# 1. データの網羅性（欠けがない）
# ---------------------------------------------------------------------------

def test_every_type_has_all_sections() -> None:
    assert set(TYPE_TEXT.keys()) == {t.type_id for t in TYPE_TABLE}
    for tid, sections in TYPE_TEXT.items():
        assert set(sections.keys()) == set(SECTION_IDS), tid


def test_flavor_tables_cover_all_keys() -> None:
    assert set(ELEMENT_FLAVOR.keys()) == {"木", "火", "土", "金", "水"}
    assert set(YINYANG_FLAVOR.keys()) == {"陽", "陰"}
    for table in (ELEMENT_FLAVOR, YINYANG_FLAVOR):
        for key, sections in table.items():
            assert set(sections.keys()) == set(SECTION_IDS), key


# ---------------------------------------------------------------------------
# 2. 合成: 3層が全て含まれる
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("t", TYPE_TABLE, ids=[t.type_id for t in TYPE_TABLE])
def test_reading_composes_three_layers(t) -> None:
    r = build_reading_for_type(t)
    assert len(r.sections) == len(SECTIONS)
    for sec in r.sections:
        # タイプ固有文 + 五行の味付け + 陰陽の味付け が連結されている
        assert TYPE_TEXT[t.type_id][sec.section_id] in sec.text
        assert ELEMENT_FLAVOR[t.五行][sec.section_id] in sec.text
        assert YINYANG_FLAVOR[t.陰陽][sec.section_id] in sec.text


# ---------------------------------------------------------------------------
# 3. 決定性
# ---------------------------------------------------------------------------

def test_reading_is_deterministic() -> None:
    d = dt.date(1990, 4, 15)
    assert get_reading(d).to_dict() == get_reading(d).to_dict()


def test_same_daystem_gives_same_reading() -> None:
    # 60日差は同じ日干支 → 同じ鑑定文
    a = get_reading(dt.date(2000, 1, 7))
    b = get_reading(dt.date(2000, 1, 7) + dt.timedelta(days=60))
    assert a.to_dict() == b.to_dict()


# ---------------------------------------------------------------------------
# 4. 内容の妥当性
# ---------------------------------------------------------------------------

def test_reading_maps_from_daystem() -> None:
    # 2000-01-07 = 甲 → you(葉/木/陽)
    r = get_reading(dt.date(2000, 1, 7))
    assert r.type_id == "you"
    assert (r.名称, r.五行, r.陰陽) == ("葉", "木", "陽")


def test_texts_use_polite_form() -> None:
    """敬体（です・ます調）で終わることを確認。"""
    r = get_reading(dt.date(2000, 1, 16))  # 癸 → 雫
    for sec in r.sections:
        assert sec.text.endswith("。")
        # 敬体の語尾を含む
        assert ("です。" in sec.text) or ("ます。" in sec.text) or ("ましょう。" in sec.text)


def test_headline_contains_name_and_element() -> None:
    r = get_reading(dt.date(2000, 1, 14))  # 辛 → 玉/金/陰
    assert "玉" in r.headline
    assert "金" in r.headline
    assert "陰" in r.headline


def test_section_titles_match_spec() -> None:
    r = get_reading(dt.date(2000, 1, 7))
    titles = [s.title for s in r.sections]
    assert titles == ["基本性格・強み・課題", "恋愛・結婚", "仕事・適職・金運", "対人関係・相性"]


# ---------------------------------------------------------------------------
# 5. JSON シリアライズ可能
# ---------------------------------------------------------------------------

def test_reading_json_serializable() -> None:
    import json
    r = get_reading(dt.datetime(1988, 11, 3, 10, 0))
    json.dumps(r.to_dict(), ensure_ascii=False)


def test_all_ten_types_are_distinct_readings() -> None:
    """10タイプの鑑定文がすべて異なる（コピペ漏れの検出）。"""
    texts = set()
    for t in TYPE_TABLE:
        r = build_reading_for_type(t)
        joined = "".join(s.text for s in r.sections)
        texts.add(joined)
    assert len(texts) == 10

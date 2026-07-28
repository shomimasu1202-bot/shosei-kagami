"""三柱の五行バランス（Phase 2.7）のユニットテスト。"""

from __future__ import annotations

import datetime as dt

import pytest

from app.engine import (
    get_five_element_balance,
    get_three_pillars,
    describe_balance,
)
from app.engine.element_balance import ELEMENTS_ORDER
from app.engine.five_elements import element_of_stem, element_of_branch


# ---------------------------------------------------------------------------
# 1. 集計の正しさ
# ---------------------------------------------------------------------------

def test_counts_total_is_six() -> None:
    b = get_five_element_balance(dt.date(1990, 4, 15))
    assert b.total == 6
    assert sum(b.counts.values()) == 6
    assert set(b.counts.keys()) == set(ELEMENTS_ORDER)


def test_counts_match_three_pillars() -> None:
    """天干3＋地支3の五行を独立に数えた結果と一致する。"""
    d = dt.date(1988, 11, 3)
    tp = get_three_pillars(d)
    expected = {e: 0 for e in ELEMENTS_ORDER}
    for s in (tp.year.year_stem_index, tp.month.month_stem_index, tp.day.day_stem_index):
        expected[element_of_stem(s)] += 1
    for br in (tp.year.year_branch_index, tp.month.month_branch_index, tp.day.day_branch_index):
        expected[element_of_branch(br)] += 1
    assert get_five_element_balance(d).counts == expected


def test_day_master_is_day_stem_element() -> None:
    d = dt.date(1990, 4, 15)  # 日干 庚 → 金
    b = get_five_element_balance(d)
    assert b.day_master == "金"
    assert b.counts["金"] >= 1  # 日主は必ず1以上


# ---------------------------------------------------------------------------
# 2. dominant / lacking の定義
# ---------------------------------------------------------------------------

def test_dominant_is_max_count() -> None:
    b = get_five_element_balance(dt.date(2001, 7, 7))
    mx = max(b.counts.values())
    assert set(b.dominant) == {e for e in ELEMENTS_ORDER if b.counts[e] == mx}


def test_lacking_is_zero_count() -> None:
    b = get_five_element_balance(dt.date(2001, 7, 7))
    assert set(b.lacking) == {e for e in ELEMENTS_ORDER if b.counts[e] == 0}
    # dominant と lacking は重ならない
    assert not (set(b.dominant) & set(b.lacking))


def test_dominant_always_exists() -> None:
    """6要素を5五行に配ると鳩ノ巣原理で必ず2以上の五行がある。"""
    for month in range(1, 13):
        b = get_five_element_balance(dt.date(1995, month, 15))
        assert len(b.dominant) >= 1
        assert max(b.counts.values()) >= 2


# ---------------------------------------------------------------------------
# 3. 個別化: 同じ日干でも生年月日で変わる
# ---------------------------------------------------------------------------

def test_same_daystem_different_balance() -> None:
    # 60日差＝同じ日柱だが、年月柱が違うため五行バランスは変わり得る
    a = get_five_element_balance(dt.date(2000, 1, 7))
    b = get_five_element_balance(dt.date(2000, 1, 7) + dt.timedelta(days=60))
    assert a.counts != b.counts


def test_deterministic() -> None:
    d = dt.date(1990, 4, 15)
    assert get_five_element_balance(d).to_dict() == get_five_element_balance(d).to_dict()


# ---------------------------------------------------------------------------
# 4. 説明文・JSON
# ---------------------------------------------------------------------------

def test_describe_balance_is_polite_and_mentions_dominant() -> None:
    b = get_five_element_balance(dt.date(1990, 4, 15))
    text = describe_balance(b)
    assert text.endswith("。")
    assert ("です。" in text) or ("ます。" in text) or ("でしょう。" in text) or ("なれます。" in text)
    # 最頻の五行名が言及される
    assert b.dominant[0] in text


def test_balance_json_serializable() -> None:
    import json
    b = get_five_element_balance(dt.datetime(1995, 8, 20, 9, 30))
    json.dumps(b.to_dict(), ensure_ascii=False)

"""三柱の五行バランス（Phase 2.7 / 蔵干対応）のユニットテスト。"""

from __future__ import annotations

import datetime as dt

import pytest

from app.engine import (
    get_five_element_balance,
    get_three_pillars,
    describe_balance,
)
from app.engine.element_balance import (
    ELEMENTS_ORDER,
    STEM_WEIGHT,
    HONKI_WEIGHT,
    CHUKI_WEIGHT,
    YOKI_WEIGHT,
)
from app.engine.hidden_stems import HIDDEN_STEMS, HONKI, CHUKI, YOKI
from app.engine.five_elements import element_of_stem, element_of_branch


# ---------------------------------------------------------------------------
# 1. 蔵干テーブルの健全性
# ---------------------------------------------------------------------------

def test_hidden_stems_cover_all_branches() -> None:
    assert set(HIDDEN_STEMS.keys()) == set(range(12))


def test_hidden_stem_honki_matches_branch_element() -> None:
    """各地支の本気の五行は、その地支自身の五行と一致する。"""
    for branch_index, hidden in HIDDEN_STEMS.items():
        honki_stem, role = hidden[0]
        assert role == HONKI
        assert element_of_stem(honki_stem) == element_of_branch(branch_index)


def test_hidden_stem_roles_are_ordered() -> None:
    """本気は先頭に1つ、以降は中気・余気のみ。"""
    for hidden in HIDDEN_STEMS.values():
        assert hidden[0][1] == HONKI
        for _, role in hidden[1:]:
            assert role in (CHUKI, YOKI)
        assert 1 <= len(hidden) <= 3


# ---------------------------------------------------------------------------
# 2. 集計（蔵干込み・重み付き）
# ---------------------------------------------------------------------------

def test_scores_sum_equals_total() -> None:
    b = get_five_element_balance(dt.date(1990, 4, 15))
    assert sum(b.scores.values()) == b.total
    assert set(b.scores.keys()) == set(ELEMENTS_ORDER)
    assert b.include_hidden_stems is True


def test_scores_match_manual_weighted_tally_without_bunya() -> None:
    """月律分野を切ると、全地支が固定蔵干（本気3/中気2/余気1）の手計算と一致する。"""
    d = dt.date(1988, 11, 3)
    tp = get_three_pillars(d)
    expected = {e: 0 for e in ELEMENTS_ORDER}
    for s in (tp.year.year_stem_index, tp.month.month_stem_index, tp.day.day_stem_index):
        expected[element_of_stem(s)] += STEM_WEIGHT
    role_w = {HONKI: HONKI_WEIGHT, CHUKI: CHUKI_WEIGHT, YOKI: YOKI_WEIGHT}
    for br in (tp.year.year_branch_index, tp.month.month_branch_index, tp.day.day_branch_index):
        for stem_idx, role in HIDDEN_STEMS[br]:
            expected[element_of_stem(stem_idx)] += role_w[role]
    got = get_five_element_balance(d, use_getsuritsu_bunya=False)
    assert got.scores == expected
    assert got.month_commander is None


def test_percentages_sum_to_100() -> None:
    for month in range(1, 13):
        b = get_five_element_balance(dt.date(1993, month, 10))
        assert sum(b.percentages.values()) == 100


def test_day_master_present_in_scores() -> None:
    b = get_five_element_balance(dt.date(1990, 4, 15))  # 日干 庚 → 金
    assert b.day_master == "金"
    assert b.scores["金"] >= STEM_WEIGHT  # 日主の天干分は必ず入る


# ---------------------------------------------------------------------------
# 3. 可視のみ（蔵干なし）は旧来の合計6カウントを再現
# ---------------------------------------------------------------------------

def test_visible_only_reproduces_six_count() -> None:
    d = dt.date(1990, 4, 15)
    b = get_five_element_balance(d, include_hidden_stems=False)
    assert b.total == 6
    assert b.include_hidden_stems is False
    # 天干3＋地支本気3（＝地支自身の五行）を各1で数えたものと一致
    tp = get_three_pillars(d)
    expected = {e: 0 for e in ELEMENTS_ORDER}
    for s in (tp.year.year_stem_index, tp.month.month_stem_index, tp.day.day_stem_index):
        expected[element_of_stem(s)] += 1
    for br in (tp.year.year_branch_index, tp.month.month_branch_index, tp.day.day_branch_index):
        expected[element_of_branch(br)] += 1
    assert b.scores == expected


def test_hidden_gives_richer_distribution_than_visible() -> None:
    """蔵干込みのほうが total（情報量）が大きい。"""
    d = dt.date(2001, 7, 7)
    full = get_five_element_balance(d, include_hidden_stems=True)
    visible = get_five_element_balance(d, include_hidden_stems=False)
    assert full.total > visible.total


# ---------------------------------------------------------------------------
# 4. dominant / lacking
# ---------------------------------------------------------------------------

def test_dominant_is_max_and_lacking_is_zero() -> None:
    b = get_five_element_balance(dt.date(2001, 7, 7))
    mx = max(b.scores.values())
    assert set(b.dominant) == {e for e in ELEMENTS_ORDER if b.scores[e] == mx}
    assert set(b.lacking) == {e for e in ELEMENTS_ORDER if b.scores[e] == 0}
    assert not (set(b.dominant) & set(b.lacking))


def test_dominant_always_exists() -> None:
    for month in range(1, 13):
        b = get_five_element_balance(dt.date(1995, month, 15))
        assert len(b.dominant) >= 1


# ---------------------------------------------------------------------------
# 5. 個別化・決定性・説明文・JSON
# ---------------------------------------------------------------------------

def test_same_daystem_different_balance() -> None:
    a = get_five_element_balance(dt.date(2000, 1, 7))
    b = get_five_element_balance(dt.date(2000, 1, 7) + dt.timedelta(days=60))
    assert a.scores != b.scores


def test_deterministic() -> None:
    d = dt.date(1990, 4, 15)
    assert get_five_element_balance(d).to_dict() == get_five_element_balance(d).to_dict()


def test_describe_balance_is_polite_and_mentions_dominant() -> None:
    b = get_five_element_balance(dt.date(1990, 4, 15))
    text = describe_balance(b)
    assert text.endswith("。")
    assert ("です。" in text) or ("ます。" in text) or ("でしょう。" in text) or ("なれます。" in text)
    assert b.dominant[0] in text
    assert "蔵干" in text  # 本格版は蔵干に言及


def test_balance_json_serializable() -> None:
    import json
    b = get_five_element_balance(dt.datetime(1995, 8, 20, 9, 30))
    json.dumps(b.to_dict(), ensure_ascii=False)

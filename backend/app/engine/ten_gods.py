"""通変星（十神）の算出。

日主（日干）から見た、ある天干との関係を10種に分類する。四柱推命の中核概念で、
五行の相生・相剋と陰陽の同異の組み合わせで決まる。

    T が日主と同じ五行:  同じ陰陽→比肩、異なる陰陽→劫財
    日主が T を生む(我生): 同→食神、異→傷官
    日主が T を剋す(我剋): 同→偏財、異→正財
    T が日主を剋す(剋我): 同→偏官(七殺)、異→正官
    T が日主を生む(生我): 同→偏印、異→印綬

五行 index: 木0 火1 土2 金3 水4（相生 = (i+1)%5、相剋 = (i+2)%5）。
天干 index の五行は index//2、陰陽は index%2（偶=陽・奇=陰）。
"""

from __future__ import annotations

# 十神の一覧（検証用）。
TEN_GODS: tuple[str, ...] = (
    "比肩", "劫財", "食神", "傷官", "偏財",
    "正財", "偏官", "正官", "偏印", "印綬",
)


def _element_index(stem_index: int) -> int:
    """天干 index → 五行 index（木0 火1 土2 金3 水4）。"""
    return stem_index // 2


def get_ten_god(day_stem_index: int, target_stem_index: int) -> str:
    """日主(day_stem_index)から見た target_stem_index の通変星を返す。"""
    dm_e = _element_index(day_stem_index)
    t_e = _element_index(target_stem_index)
    same_polarity = (day_stem_index % 2) == (target_stem_index % 2)

    if t_e == dm_e:
        return "比肩" if same_polarity else "劫財"
    if (dm_e + 1) % 5 == t_e:            # 我生（日主が生む）
        return "食神" if same_polarity else "傷官"
    if (dm_e + 2) % 5 == t_e:            # 我剋（日主が剋す）
        return "偏財" if same_polarity else "正財"
    if (t_e + 2) % 5 == dm_e:            # 剋我（相手が剋す）
        return "偏官" if same_polarity else "正官"
    # 生我（相手が生む）: (t_e + 1) % 5 == dm_e
    return "偏印" if same_polarity else "印綬"

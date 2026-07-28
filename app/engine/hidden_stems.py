"""蔵干（地支に隠れた天干）テーブル。

四柱推命では、地支（十二支）はそれぞれ内部に 1〜3 個の天干を蔵している。
本気（主）・中気・余気の順に影響が強い。本モジュールは淵海子平系の
標準的な蔵干配当を用いる（広く流布する固定表）。

出典・参照:
    - 淵海子平ほかに載る「地支蔵干（人元）」の標準表
    - 各地支の本気の五行は、その地支自身の五行と一致する
      （例: 子=水=本気 癸[水]、寅=木=本気 甲[木]）

注: 本フェーズは本気/中気/余気の固定重みで数える。月律分野蔵干
    （節入りからの経過日数で本気/中気/余気の比率を変える）は後続の拡張余地。
"""

from __future__ import annotations

# 蔵干の役割。影響の強い順。
HONKI = "本気"
CHUKI = "中気"
YOKI = "余気"

# 地支 index (0=子 … 11=亥) → [(天干 index, 役割), ...]（本気を先頭に）。
# 天干: 甲0 乙1 丙2 丁3 戊4 己5 庚6 辛7 壬8 癸9
HIDDEN_STEMS: dict[int, tuple[tuple[int, str], ...]] = {
    0:  ((9, HONKI),),                          # 子: 癸
    1:  ((5, HONKI), (9, CHUKI), (7, YOKI)),    # 丑: 己・癸・辛
    2:  ((0, HONKI), (2, CHUKI), (4, YOKI)),    # 寅: 甲・丙・戊
    3:  ((1, HONKI),),                          # 卯: 乙
    4:  ((4, HONKI), (1, CHUKI), (9, YOKI)),    # 辰: 戊・乙・癸
    5:  ((2, HONKI), (6, CHUKI), (4, YOKI)),    # 巳: 丙・庚・戊
    6:  ((3, HONKI), (5, CHUKI)),               # 午: 丁・己
    7:  ((5, HONKI), (3, CHUKI), (1, YOKI)),    # 未: 己・丁・乙
    8:  ((6, HONKI), (8, CHUKI), (4, YOKI)),    # 申: 庚・壬・戊
    9:  ((7, HONKI),),                          # 酉: 辛
    10: ((4, HONKI), (7, CHUKI), (3, YOKI)),    # 戌: 戊・辛・丁
    11: ((8, HONKI), (0, CHUKI)),               # 亥: 壬・甲
}


def hidden_stems_of_branch(branch_index: int) -> tuple[tuple[int, str], ...]:
    """地支 index → 蔵干のリスト [(天干 index, 役割), ...]。"""
    return HIDDEN_STEMS[branch_index]

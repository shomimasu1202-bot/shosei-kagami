"""月律分野蔵干（人元司令分野）テーブル。

月柱の地支（月令）だけは、蔵干のどれが「司令（その月を主宰する天干）」かが、
節入りからの経過日数で変わる。各蔵干に配当された日数（分野）を持ち、
生誕日が節入りから何日目かで司令の天干が決まる。

例（寅月＝立春）: 節入りから 0〜7日は 戊（余気）、7〜14日は 丙（中気）、
14〜30日は 甲（本気）が司令する。

出典・参照:
    - 三命通会・淵海子平などに載る「人元司令分野」の日数配当
    - 各月を30日に正規化した、広く流布する配当表を用いる
    - 年柱・日柱の地支は月律を用いず、固定の蔵干表（hidden_stems.py）を使う

注: 司令の判定に用いる「節入り」時刻は solar.py の太陽黄経計算（精度 ~数分）に基づく。
"""

from __future__ import annotations

# 役割（hidden_stems.py と同じ語）。
from .hidden_stems import HONKI, CHUKI, YOKI

# 地支 index (0=子 … 11=亥) → ((天干 index, 役割, 日数), ...)（余気→中気→本気の順、合計30日）。
# 天干: 甲0 乙1 丙2 丁3 戊4 己5 庚6 辛7 壬8 癸9
GETSURITSU_BUNYA: dict[int, tuple[tuple[int, str, int], ...]] = {
    2:  ((4, YOKI, 7), (2, CHUKI, 7), (0, HONKI, 16)),   # 寅: 戊7 丙7 甲16
    3:  ((0, YOKI, 10), (1, HONKI, 20)),                 # 卯: 甲10 乙20
    4:  ((1, YOKI, 9), (9, CHUKI, 3), (4, HONKI, 18)),   # 辰: 乙9 癸3 戊18
    5:  ((4, YOKI, 5), (6, CHUKI, 9), (2, HONKI, 16)),   # 巳: 戊5 庚9 丙16
    6:  ((2, YOKI, 10), (5, CHUKI, 9), (3, HONKI, 11)),  # 午: 丙10 己9 丁11
    7:  ((3, YOKI, 9), (1, CHUKI, 3), (5, HONKI, 18)),   # 未: 丁9 乙3 己18
    8:  ((4, YOKI, 7), (8, CHUKI, 7), (6, HONKI, 16)),   # 申: 戊7 壬7 庚16
    9:  ((6, YOKI, 10), (7, HONKI, 20)),                 # 酉: 庚10 辛20
    10: ((7, YOKI, 9), (3, CHUKI, 3), (4, HONKI, 18)),   # 戌: 辛9 丁3 戊18
    11: ((4, YOKI, 7), (0, CHUKI, 5), (8, HONKI, 18)),   # 亥: 戊7 甲5 壬18
    0:  ((8, YOKI, 10), (9, HONKI, 20)),                 # 子: 壬10 癸20
    1:  ((9, YOKI, 9), (7, CHUKI, 3), (5, HONKI, 18)),   # 丑: 癸9 辛3 己18
}

# 各月の合計日数（正規化）。
BUNYA_TOTAL_DAYS = 30


def commanding_stem(branch_index: int, days_since_setsu: float) -> tuple[int, str]:
    """月支と節入りからの経過日数 → 司令する (天干 index, 役割)。

    経過日数が配当を超える場合（実際の節月は30〜31日超あり得る）は本気に丸める。
    負の値は先頭（余気）に丸める。
    """
    segments = GETSURITSU_BUNYA[branch_index]
    cumulative = 0
    for stem_index, role, days in segments:
        cumulative += days
        if days_since_setsu < cumulative:
            return stem_index, role
    # 末尾（本気）に丸める
    return segments[-1][0], segments[-1][1]

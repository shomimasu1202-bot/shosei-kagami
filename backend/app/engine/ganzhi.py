"""日柱（日干支）の算出。

日干支は 60 日周期で連続する。ある基準日（アンカー）からの経過日数を
mod 60 することで、任意の civil date の日干支インデックスを求める。

== アンカーの較正 ==
アンカー日付   : 2000-01-07（西暦・グレゴリオ暦）
その日干支     : 甲子（きのえね / jiǎzǐ）= 60干支サイクルの先頭（index 0）
出典・較正根拠 :
    日干支とユリウス通日(JDN)の関係は次の式で与えられる（広く用いられる万年暦の式）:
        日干 index = (JDN + 9)  mod 10   (0=甲 ... 9=癸)
        日支 index = (JDN + 1)  mod 12   (0=子 ... 11=亥)
    この式を用いると、
        1900-01-01 → 甲戌   （多くの万年暦・干支表で確認できる古典的な基準日）
        2000-01-07 → 甲子   （60サイクルの先頭。本モジュールのアンカー）
    の2点で相互に整合する。本実装では扱いやすい甲子(index 0)である
    2000-01-07 をアンカー定数として採用する。
    ※ Python の datetime.date はグレゴリオ暦（先発グレゴリオ暦）で日数差を計算するため、
      アンカーからの date 差分をそのまま mod 60 して用いてよい。

参考:
    - 干支（Wikipedia 日本語版）「日の干支」節に載る換算式・基準日
    - 一般的な万年暦（perpetual calendar）における日干支の連続性
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, asdict

# 十干（じっかん）: 甲(0) 乙(1) 丙(2) 丁(3) 戊(4) 己(5) 庚(6) 辛(7) 壬(8) 癸(9)
STEMS: tuple[str, ...] = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")

# 十二支（じゅうにし）: 子(0) 丑(1) 寅(2) 卯(3) 辰(4) 巳(5) 午(6) 未(7) 申(8) 酉(9) 戌(10) 亥(11)
BRANCHES: tuple[str, ...] = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")

# --- アンカー定数（上記コメントの通り較正済み） ---
ANCHOR_DATE: _dt.date = _dt.date(2000, 1, 7)
ANCHOR_GANZHI60: int = 0  # 甲子 = 60干支サイクルの先頭

# 深夜（子の刻）境界の既定オフセット時刻。late_night_boundary=True のとき
# この時刻以降を翌日の干支として扱う。
LATE_NIGHT_HOUR: int = 23


@dataclass(frozen=True)
class DayPillar:
    """日柱（日干支）。JSON シリアライズ可能。"""

    day_stem_index: int   # 日干 index (0〜9)
    day_branch_index: int  # 日支 index (0〜11)
    day_stem_name: str    # 日干名（例: 甲）
    day_branch_name: str   # 日支名（例: 子）

    @property
    def ganzhi60_index(self) -> int:
        """60干支サイクル内のインデックス (0〜59)。"""
        # 中国剰余の対応（stem10, branch12）から 60 の値を復元。
        # 甲子=0 を先頭に、stem は10周期・branch は12周期。
        for i in range(60):
            if i % 10 == self.day_stem_index and i % 12 == self.day_branch_index:
                return i
        raise AssertionError("unreachable")  # pragma: no cover

    @property
    def ganzhi_name(self) -> str:
        """日干支の名称（例: 甲子）。"""
        return f"{self.day_stem_name}{self.day_branch_name}"

    def to_dict(self) -> dict:
        return asdict(self)


def _resolve_civil_date(
    value: _dt.date | _dt.datetime,
    *,
    late_night_boundary: bool,
) -> _dt.date:
    """入力を「干支を割り当てる civil date」に正規化する。

    - date が渡された場合はそのまま（時刻情報なし）。
    - datetime が渡され late_night_boundary=True かつ 23時以降の場合は翌日扱い。
    - late_night_boundary=False の場合は常に civil midnight 基準（=その日の日付）。
    """
    if isinstance(value, _dt.datetime):
        base = value.date()
        if late_night_boundary and value.hour >= LATE_NIGHT_HOUR:
            return base + _dt.timedelta(days=1)
        return base
    if isinstance(value, _dt.date):
        # 純粋な date には時刻がないため late_night_boundary は影響しない。
        return value
    raise TypeError(f"date または datetime を渡してください: {type(value)!r}")


def get_day_pillar(
    value: _dt.date | _dt.datetime,
    *,
    late_night_boundary: bool = False,
) -> DayPillar:
    """civil date から日柱（日干支）を算出する。

    Args:
        value: 西暦の生年月日（datetime.date または datetime.datetime）。
        late_night_boundary: True かつ datetime の時刻が 23時以降のとき、
            翌日の干支（子の刻）として扱う。既定は civil midnight 基準の False。

    Returns:
        DayPillar（日干 index / 日支 index / 日干名 / 日支名）。
    """
    civil = _resolve_civil_date(value, late_night_boundary=late_night_boundary)
    days_from_anchor = (civil - ANCHOR_DATE).days
    ganzhi60 = (ANCHOR_GANZHI60 + days_from_anchor) % 60
    stem_index = ganzhi60 % 10
    branch_index = ganzhi60 % 12
    return DayPillar(
        day_stem_index=stem_index,
        day_branch_index=branch_index,
        day_stem_name=STEMS[stem_index],
        day_branch_name=BRANCHES[branch_index],
    )

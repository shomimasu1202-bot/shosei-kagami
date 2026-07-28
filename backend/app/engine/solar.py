"""太陽黄経（solar longitude）と二十四節気のうち「節」の算出。

四柱推命では、年柱は立春（太陽黄経 315°）で切り替わり、月柱は 12 の「節」
（節気のうち節入りの側）で切り替わる。これらは暦日ではなく太陽の黄経で定義される
ため、天文計算が必要になる。

本モジュールは外部ライブラリに依存せず、Meeus『Astronomical Algorithms』
(2nd ed., ch.25) の低精度式で太陽の視黄経を計算する。精度は約 0.01°
（時間にして約 15 分）。占い用途では十分だが、節入りの瞬間の前後 15 分程度に
生まれた場合は月柱・年柱が入れ替わり得る点に注意（境界の限界として明記する）。

タイムゾーンは日本標準時 (JST, UTC+9) を既定とする。JST は現在サマータイムを
採用していないため固定オフセットで扱う。
"""

from __future__ import annotations

import datetime as _dt
import math

# 日本標準時（固定 +9:00）。zoneinfo/tzdata に依存しないため fixed offset を用いる。
JST = _dt.timezone(_dt.timedelta(hours=9), name="JST")
UTC = _dt.timezone.utc

# 12 の「節」の太陽黄経（度）と、その節が始める月の名称・地支。
# 立春(315°)=寅月 から始まり 30° ごと。
# (太陽黄経, 節の名称, 月の順序 k [0=寅], 地支 index)
SOLAR_TERM_LONGITUDES: tuple[float, ...] = (
    315.0, 345.0, 15.0, 45.0, 75.0, 105.0,
    135.0, 165.0, 195.0, 225.0, 255.0, 285.0,
)
# 月の順序 k (0=寅) → 節の名称
SOLAR_TERM_NAMES: tuple[str, ...] = (
    "立春", "啓蟄", "清明", "立夏", "芒種", "小暑",
    "立秋", "白露", "寒露", "立冬", "大雪", "小寒",
)

# 太陽の平均日運動（度/日）。ニュートン法の近傍導関数として用いる。
_DEG_PER_DAY = 0.98564736


def delta_t_seconds(year: float) -> float:
    """ΔT（TT − UT1）の近似値[秒]。Espenak & Meeus (2006) の多項式。

    1900〜2150 をカバー。占い用途では十数分の精度で足りるため、ΔT の数十秒の
    誤差は無視できるが、正しさのため補正しておく。
    """
    y = year
    if y < 1920:
        t = y - 1900
        return (-2.79 + 1.494119 * t - 0.0598939 * t**2
                + 0.0061966 * t**3 - 0.000197 * t**4)
    if y < 1941:
        t = y - 1920
        return 21.20 + 0.84493 * t - 0.076100 * t**2 + 0.0020936 * t**3
    if y < 1961:
        t = y - 1950
        return 29.07 + 0.407 * t - t**2 / 233 + t**3 / 2547
    if y < 1986:
        t = y - 1975
        return 45.45 + 1.067 * t - t**2 / 260 - t**3 / 718
    if y < 2005:
        t = y - 2000
        return (63.86 + 0.3345 * t - 0.060374 * t**2 + 0.0017275 * t**3
                + 0.000651814 * t**4 + 0.00002373599 * t**5)
    if y < 2050:
        t = y - 2000
        return 62.92 + 0.32217 * t + 0.005589 * t**2
    if y < 2150:
        return -20 + 32 * ((y - 1820) / 100) ** 2 - 0.5628 * (2150 - y)
    # 範囲外は 2150 の外挿
    return -20 + 32 * ((y - 1820) / 100) ** 2


def gregorian_to_jd(year: int, month: int, day: float) -> float:
    """グレゴリオ暦（先発グレゴリオ暦）→ ユリウス通日。day は小数（時刻）を含む。"""
    if month <= 2:
        year -= 1
        month += 12
    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)
    return (math.floor(365.25 * (year + 4716))
            + math.floor(30.6001 * (month + 1))
            + day + b - 1524.5)


def datetime_to_jd(dt_utc: _dt.datetime) -> float:
    """UTC の datetime → ユリウス通日 (UT)。"""
    if dt_utc.tzinfo is None:
        raise ValueError("datetime_to_jd には tz-aware な datetime が必要")
    u = dt_utc.astimezone(UTC)
    day_frac = (u.day
                + u.hour / 24
                + u.minute / 1440
                + u.second / 86400
                + u.microsecond / 86_400_000_000)
    return gregorian_to_jd(u.year, u.month, day_frac)


def jd_to_datetime_utc(jd: float) -> _dt.datetime:
    """ユリウス通日 (UT) → UTC の datetime。"""
    jd += 0.5
    z = math.floor(jd)
    f = jd - z
    if z < 2299161:
        a = z
    else:
        alpha = math.floor((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - math.floor(alpha / 4)
    b = a + 1524
    c = math.floor((b - 122.1) / 365.25)
    d = math.floor(365.25 * c)
    e = math.floor((b - d) / 30.6001)
    day_with_frac = b - d - math.floor(30.6001 * e) + f
    day = int(day_with_frac)
    frac = day_with_frac - day
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715

    total_seconds = round(frac * 86400)
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    base = _dt.datetime(year, month, day, tzinfo=UTC)
    return base + _dt.timedelta(hours=hours, minutes=minutes, seconds=seconds)


def solar_longitude(jd_ut: float) -> float:
    """視黄経（apparent solar longitude, 度, 0〜360）を返す。

    入力は UT のユリウス通日。内部で ΔT を用いて力学時 (TT) に変換して計算する。
    Meeus ch.25 の低精度式（精度 ~0.01°）。
    """
    approx_year = (jd_ut - 2451545.0) / 365.25 + 2000.0
    jde = jd_ut + delta_t_seconds(approx_year) / 86400.0
    t = (jde - 2451545.0) / 36525.0  # J2000 からのユリウス世紀

    # 幾何平均黄経・平均近点角（度）
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    m_rad = math.radians(m % 360.0)

    # 中心差（equation of center, 度）
    c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m_rad)
         + (0.019993 - 0.000101 * t) * math.sin(2 * m_rad)
         + 0.000289 * math.sin(3 * m_rad))

    true_long = l0 + c
    # 章動・光行差を含めた視黄経へ
    omega = 125.04 - 1934.136 * t
    apparent = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    return apparent % 360.0


def find_solar_term(year: int, target_longitude: float) -> _dt.datetime:
    """指定した太陽黄経になる瞬間のうち、グレゴリオ暦 `year` 内の occurrence を返す。

    返り値は JST の tz-aware datetime。ニュートン法で反復。
    """
    target = target_longitude % 360.0
    jd0 = gregorian_to_jd(year, 1, 1.0)  # その年の 1/1 00:00 UT
    # 1/1 の太陽黄経は約 280°。そこからの黄経差で初期推定日を得る。
    dl = (target - 280.0) % 360.0
    jd = jd0 + dl / _DEG_PER_DAY

    for _ in range(10):
        lon = solar_longitude(jd)
        # target との差を (-180, 180] に正規化
        diff = ((lon - target + 180.0) % 360.0) - 180.0
        jd -= diff / _DEG_PER_DAY
        if abs(diff) < 1e-6:
            break

    return jd_to_datetime_utc(jd).astimezone(JST)


def normalize_to_jst(value: _dt.date | _dt.datetime, *, assumed_hour: int = 12) -> _dt.datetime:
    """入力を JST の tz-aware datetime に正規化する。

    - date のみ: 時刻不明として `assumed_hour`（既定 12:00 JST）を仮定する。
      節入りの当日に生まれた場合の誤差を最小化するため正午を既定とする。
    - naive datetime: JST とみなす。
    - aware datetime: JST に変換する。
    """
    if isinstance(value, _dt.datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=JST)
        return value.astimezone(JST)
    if isinstance(value, _dt.date):
        return _dt.datetime(value.year, value.month, value.day, assumed_hour, 0, tzinfo=JST)
    raise TypeError(f"date または datetime を渡してください: {type(value)!r}")

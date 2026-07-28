"""任意の生年月日で算出結果を表示するサンプルスクリプト。

実行:
    python -m scripts.sample
    python -m scripts.sample 1990-04-15 2001-11-03
    python -m scripts.sample "1990-04-15T14:20"   # 時刻を付けると四柱
"""

from __future__ import annotations

import datetime as dt
import sys

from app.engine import get_five_element_profile, get_type, get_four_pillars, get_reading

DEFAULT_DATES = [
    "1990-04-15",
    "1985-12-31",
    "2000-02-29",
    "2012-07-07",
    "2024-02-04",  # 立春当日（正午仮定）
]


def _parse(s: str) -> dt.date | dt.datetime:
    """'YYYY-MM-DD' は date、'YYYY-MM-DDTHH:MM' は datetime として解釈。"""
    try:
        return dt.datetime.fromisoformat(s)
    except ValueError:
        return dt.date.fromisoformat(s)


def show(date_str: str) -> None:
    d = _parse(date_str)
    fp = get_four_pillars(d)
    prof = get_five_element_profile(d)
    t = get_type(d)
    print(f"■ {date_str}")
    print(f"   年柱 : {fp.year.ganzhi_name}（立春基準 {fp.year.astrological_year}年）")
    print(f"   月柱 : {fp.month.ganzhi_name}（{fp.month.solar_term_name}節・{fp.month.month_branch_name}月）")
    print(f"   日柱 : {fp.day.ganzhi_name}（日干 {fp.day.day_stem_name} / 日支 {fp.day.day_branch_name}）")
    if fp.hour is not None:
        print(f"   時柱 : {fp.hour.ganzhi_name}（{fp.hour.time_range}）")
    bal = get_reading(d).element_balance
    cs = "・".join(f"{e}{bal.percentages[e]}%" for e in ("木", "火", "土", "金", "水"))
    print(f"   五行バランス(蔵干込): {cs}（{bal.comment}）")
    print(f"   五行 : {prof.五行} ／ 陰陽 : {prof.陰陽}（日干ベース）")
    print(f"   タイプ: {t.名称}（{t.読み}） [{t.type_id}]")
    print(f"          {t.一言特徴}")
    r = get_reading(d)
    for sec in r.sections:
        print(f"   【{sec.title}】")
        print(f"     {sec.text}")
    g = r.compatibility_guide
    print(f"   相性 : 好相性(相生) {'・'.join(g.best)} ／ 要注意(相剋) {'・'.join(g.caution)}")
    print()


def main() -> None:
    dates = sys.argv[1:] or DEFAULT_DATES
    for d in dates:
        show(d)


if __name__ == "__main__":
    main()

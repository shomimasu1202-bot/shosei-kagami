"""任意の生年月日で算出結果を表示するサンプルスクリプト。

実行:
    python -m scripts.sample
    python -m scripts.sample 1990-04-15 2001-11-03
"""

from __future__ import annotations

import datetime as dt
import sys

from app.engine import get_five_element_profile, get_type, get_three_pillars

DEFAULT_DATES = [
    "1990-04-15",
    "1985-12-31",
    "2000-02-29",
    "2012-07-07",
    "2024-02-04",  # 立春当日（正午仮定）
]


def show(date_str: str) -> None:
    d = dt.date.fromisoformat(date_str)
    tp = get_three_pillars(d)
    prof = get_five_element_profile(d)
    t = get_type(d)
    print(f"■ {date_str}")
    print(f"   年柱 : {tp.year.ganzhi_name}（立春基準 {tp.year.astrological_year}年）")
    print(f"   月柱 : {tp.month.ganzhi_name}（{tp.month.solar_term_name}節・{tp.month.month_branch_name}月）")
    print(f"   日柱 : {tp.day.ganzhi_name}（日干 {tp.day.day_stem_name} / 日支 {tp.day.day_branch_name}）")
    print(f"   五行 : {prof.五行} ／ 陰陽 : {prof.陰陽}（日干ベース）")
    print(f"   タイプ: {t.名称}（{t.読み}） [{t.type_id}]")
    print(f"          {t.一言特徴}")
    print()


def main() -> None:
    dates = sys.argv[1:] or DEFAULT_DATES
    for d in dates:
        show(d)


if __name__ == "__main__":
    main()

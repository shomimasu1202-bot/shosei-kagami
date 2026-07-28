"""掌星鑑オリジナル10タイプ 対応表と写像。

★ 確定表（改変禁止）: 日干（十干）と 1 対 1 で対応する。
   名称・読み・五行・陰陽・一言特徴は変更しないこと。

   甲 → you    葉  よう   木 陽
   乙 → fuji   藤  ふじ   木 陰
   丙 → asahi  旭  あさひ 火 陽
   丁 → hotaru 蛍  ほたる 火 陰
   戊 → mine   嶺  みね   土 陽
   己 → sono   苑  その   土 陰
   庚 → rin    鈴  りん   金 陽
   辛 → gyoku  玉  ぎょく 金 陰
   壬 → minato 湊  みなと 水 陽
   癸 → shizuku 雫 しずく 水 陰

タイプ体系は公有である干支・五行を土台にした掌星鑑オリジナル。
既存の占いブランドの名称・タイプ名・鑑定文は使用していない。
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, asdict

from .ganzhi import get_day_pillar


@dataclass(frozen=True)
class ShoseiType:
    """掌星鑑タイプ。JSON シリアライズ可能。"""

    type_id: str
    名称: str
    読み: str
    五行: str
    陰陽: str
    一言特徴: str

    def to_dict(self) -> dict:
        return asdict(self)


# 日干 index (0〜9) → ShoseiType。STEMS の並び（甲=0 ... 癸=9）に一致させる。
TYPE_TABLE: tuple[ShoseiType, ...] = (
    ShoseiType("you", "葉", "よう", "木", "陽",
               "伸びゆく葉。まっすぐな成長力と素直さ。"),                 # 甲
    ShoseiType("fuji", "藤", "ふじ", "木", "陰",
               "しなやかに咲く藤。柔軟で人とつながる力。"),               # 乙
    ShoseiType("asahi", "旭", "あさひ", "火", "陽",
               "朝の日ざし。周りを明るくする温かさ。"),                   # 丙
    ShoseiType("hotaru", "蛍", "ほたる", "火", "陰",
               "そっと光る蛍。細やかな気配りと内なる温もり。"),           # 丁
    ShoseiType("mine", "嶺", "みね", "土", "陽",
               "広がる山の頂。揺るがない包容力と安定感。"),               # 戊
    ShoseiType("sono", "苑", "その", "土", "陰",
               "草木を育てる庭。人を丁寧に育てる優しさ。"),               # 己
    ShoseiType("rin", "鈴", "りん", "金", "陽",
               "澄んだ鈴の音。まっすぐで潔い決断力。"),                   # 庚
    ShoseiType("gyoku", "玉", "ぎょく", "金", "陰",
               "磨かれた宝玉。繊細な美意識と気品。"),                     # 辛
    ShoseiType("minato", "湊", "みなと", "水", "陽",
               "人が集う水辺。おおらかで人を惹きつける。"),               # 壬
    ShoseiType("shizuku", "雫", "しずく", "水", "陰",
               "静かに落ちる露。豊かな感受性と直感。"),                   # 癸
)

# 日干 index → type_id の 1 対 1 写像。
STEM_INDEX_TO_TYPE_ID: dict[int, str] = {
    i: t.type_id for i, t in enumerate(TYPE_TABLE)
}


def type_of_stem(stem_index: int) -> ShoseiType:
    """十干 index → 掌星鑑タイプ。"""
    return TYPE_TABLE[stem_index]


def get_type(
    value: _dt.date | _dt.datetime,
    *,
    late_night_boundary: bool = False,
) -> ShoseiType:
    """生年月日 → 掌星鑑タイプ（日干ベース）。"""
    pillar = get_day_pillar(value, late_night_boundary=late_night_boundary)
    return type_of_stem(pillar.day_stem_index)

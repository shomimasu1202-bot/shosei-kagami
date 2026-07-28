"""掌星鑑 計算エンジン (Phase 1)。

公開API:
    get_day_pillar(date, *, late_night_boundary=False) -> DayPillar
    get_five_element_profile(date, *, late_night_boundary=False) -> FiveElementProfile
    get_type(date, *, late_night_boundary=False) -> ShoseiType

いずれも JSON シリアライズ可能な dataclass を返す（.to_dict() で dict 化）。
"""

from .ganzhi import (
    STEMS,
    BRANCHES,
    DayPillar,
    get_day_pillar,
)
from .five_elements import (
    FiveElementProfile,
    STEM_TO_ELEMENT,
    STEM_TO_YINYANG,
    BRANCH_TO_ELEMENT,
    get_five_element_profile,
)
from .type_table import (
    ShoseiType,
    TYPE_TABLE,
    get_type,
)

__all__ = [
    "STEMS",
    "BRANCHES",
    "DayPillar",
    "get_day_pillar",
    "FiveElementProfile",
    "STEM_TO_ELEMENT",
    "STEM_TO_YINYANG",
    "BRANCH_TO_ELEMENT",
    "get_five_element_profile",
    "ShoseiType",
    "TYPE_TABLE",
    "get_type",
]

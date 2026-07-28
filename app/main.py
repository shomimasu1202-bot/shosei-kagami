"""掌星鑑 FastAPI アプリ（Phase 1）。

Phase 1 では日柱ベースの計算エンジンをHTTPで公開する。
起動: uvicorn app.main:app --reload
"""

from __future__ import annotations

import datetime as _dt

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .engine import (
    get_day_pillar,
    get_five_element_profile,
    get_type,
    get_year_pillar,
    get_month_pillar,
    get_three_pillars,
    get_reading,
    get_compatibility,
    get_five_element_balance,
)

app = FastAPI(
    title="掌星鑑 API",
    version="0.1.0",
    description="生年月日 → 日干支・五行 → 掌星鑑オリジナル10タイプ（Phase 1）",
)


class BirthdateQuery(BaseModel):
    birthdate: _dt.date = Field(..., description="西暦の生年月日 (YYYY-MM-DD)")
    late_night_boundary: bool = Field(
        False,
        description="True かつ 23時以降のとき翌日の干支（子の刻）として扱う",
    )


class BirthDatetimeQuery(BaseModel):
    """年柱・月柱は時刻に依存し得るため、日時での指定を受け付ける。"""

    birthdate: _dt.date = Field(..., description="西暦の生年月日 (YYYY-MM-DD)")
    birthtime: _dt.time | None = Field(
        None, description="出生時刻 (HH:MM, JST)。不明なら省略可（正午を仮定）"
    )
    late_night_boundary: bool = Field(
        False, description="日柱の子の刻境界（時刻指定時のみ有効）"
    )

    def to_value(self) -> _dt.date | _dt.datetime:
        if self.birthtime is None:
            return self.birthdate
        return _dt.datetime.combine(self.birthdate, self.birthtime)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "phase": 1}


@app.post("/day-pillar")
def day_pillar(q: BirthdateQuery) -> dict:
    return get_day_pillar(
        q.birthdate, late_night_boundary=q.late_night_boundary
    ).to_dict()


@app.post("/five-element-profile")
def five_element_profile(q: BirthdateQuery) -> dict:
    return get_five_element_profile(
        q.birthdate, late_night_boundary=q.late_night_boundary
    ).to_dict()


@app.post("/type")
def shosei_type(q: BirthdateQuery) -> dict:
    return get_type(
        q.birthdate, late_night_boundary=q.late_night_boundary
    ).to_dict()


@app.post("/year-pillar")
def year_pillar(q: BirthDatetimeQuery) -> dict:
    return get_year_pillar(q.to_value()).to_dict()


@app.post("/month-pillar")
def month_pillar(q: BirthDatetimeQuery) -> dict:
    return get_month_pillar(q.to_value()).to_dict()


@app.post("/three-pillars")
def three_pillars(q: BirthDatetimeQuery) -> dict:
    return get_three_pillars(
        q.to_value(), late_night_boundary=q.late_night_boundary
    ).to_dict()


@app.post("/five-element-balance")
def five_element_balance(q: BirthDatetimeQuery) -> dict:
    """三柱（年・月・日）の五行バランス。"""
    return get_five_element_balance(
        q.to_value(), late_night_boundary=q.late_night_boundary
    ).to_dict()


class CompatibilityQuery(BaseModel):
    """2人の相性診断。birthdate_a から見た視点で返す。"""

    birthdate_a: _dt.date = Field(..., description="1人目の生年月日")
    birthdate_b: _dt.date = Field(..., description="2人目の生年月日")


@app.post("/compatibility")
def compatibility(q: CompatibilityQuery) -> dict:
    """2人の相性（五行の相生・相剋ベース）。"""
    return get_compatibility(q.birthdate_a, q.birthdate_b).to_dict()


@app.post("/reading")
def reading(q: BirthdateQuery) -> dict:
    """生年月日 → 鑑定文（基本性格・恋愛・仕事の3セクション）。"""
    return get_reading(
        q.birthdate, late_night_boundary=q.late_night_boundary
    ).to_dict()


@app.get("/type")
def shosei_type_get(birthdate: str) -> dict:
    """GET でも試せる簡易エンドポイント (?birthdate=YYYY-MM-DD)。"""
    try:
        d = _dt.date.fromisoformat(birthdate)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return get_type(d).to_dict()

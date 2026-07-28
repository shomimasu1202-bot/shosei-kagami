"""掌星鑑 FastAPI アプリ（Phase 1）。

Phase 1 では日柱ベースの計算エンジンをHTTPで公開する。
起動: uvicorn app.main:app --reload
"""

from __future__ import annotations

import datetime as _dt

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .engine import get_day_pillar, get_five_element_profile, get_type

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


@app.get("/type")
def shosei_type_get(birthdate: str) -> dict:
    """GET でも試せる簡易エンドポイント (?birthdate=YYYY-MM-DD)。"""
    try:
        d = _dt.date.fromisoformat(birthdate)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return get_type(d).to_dict()

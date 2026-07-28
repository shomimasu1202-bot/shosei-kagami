"""FastAPI エンドポイントのスモークテスト。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_type_endpoint_post() -> None:
    r = client.post("/type", json={"birthdate": "2000-01-07"})
    assert r.status_code == 200
    body = r.json()
    assert body["type_id"] == "you"
    assert body["名称"] == "葉"
    assert body["五行"] == "木"
    assert body["陰陽"] == "陽"


def test_type_endpoint_get() -> None:
    r = client.get("/type", params={"birthdate": "2000-01-16"})  # 癸 → 雫
    assert r.status_code == 200
    assert r.json()["type_id"] == "shizuku"


def test_day_pillar_endpoint() -> None:
    r = client.post("/day-pillar", json={"birthdate": "2000-01-01"})
    assert r.status_code == 200
    body = r.json()
    assert body["day_stem_name"] == "戊"
    assert body["day_branch_name"] == "午"


def test_invalid_date_returns_422() -> None:
    r = client.get("/type", params={"birthdate": "not-a-date"})
    assert r.status_code == 422


def test_three_pillars_endpoint() -> None:
    r = client.post("/three-pillars", json={"birthdate": "2024-02-10"})
    assert r.status_code == 200
    body = r.json()
    assert body["year"]["year_stem_name"] + body["year"]["year_branch_name"] == "甲辰"
    assert body["month"]["month_stem_name"] + body["month"]["month_branch_name"] == "丙寅"


def test_year_pillar_endpoint_with_time() -> None:
    # 立春当日 2024-02-04、夜（立春後）は甲辰年
    r = client.post(
        "/year-pillar", json={"birthdate": "2024-02-04", "birthtime": "20:00"}
    )
    assert r.status_code == 200
    b = r.json()
    assert b["year_stem_name"] + b["year_branch_name"] == "甲辰"

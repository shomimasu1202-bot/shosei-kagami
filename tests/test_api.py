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

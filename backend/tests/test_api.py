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


def test_reading_endpoint() -> None:
    r = client.post("/reading", json={"birthdate": "2000-01-07"})  # 甲 → you
    assert r.status_code == 200
    body = r.json()
    assert body["type_id"] == "you"
    assert len(body["sections"]) == 5  # 4静的 + 五行バランス
    assert body["sections"][0]["title"] == "基本性格・強み・課題"
    assert body["sections"][1]["title"] == "五行バランス"
    assert body["sections"][-1]["title"] == "対人関係・相性"
    assert body["sections"][0]["text"]  # 非空
    assert "best" in body["compatibility_guide"]
    assert body["element_balance"]["include_hidden_stems"] is True
    assert sum(body["element_balance"]["percentages"].values()) == 100


def test_cors_header_present() -> None:
    r = client.post(
        "/type",
        json={"birthdate": "2000-01-07"},
        headers={"Origin": "http://localhost:8081"},
    )
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "*"


def test_reading_endpoint_with_time_uses_four_pillars() -> None:
    r = client.post("/reading", json={"birthdate": "2000-01-07", "birthtime": "10:00"})
    assert r.status_code == 200
    assert r.json()["element_balance"]["pillar_count"] == 4


def test_hour_pillar_endpoint() -> None:
    r = client.post("/hour-pillar", json={"birthdate": "2000-01-07", "birthtime": "10:00"})
    assert r.status_code == 200
    b = r.json()
    assert b["hour_stem_name"] + b["hour_branch_name"] == "己巳"


def test_hour_pillar_requires_time() -> None:
    r = client.post("/hour-pillar", json={"birthdate": "2000-01-07"})
    assert r.status_code == 422


def test_four_pillars_endpoint_with_and_without_time() -> None:
    r1 = client.post("/four-pillars", json={"birthdate": "2000-01-07", "birthtime": "10:00"})
    assert r1.status_code == 200
    assert r1.json()["hour"]["hour_branch_name"] == "巳"
    r2 = client.post("/four-pillars", json={"birthdate": "2000-01-07"})
    assert r2.status_code == 200
    assert r2.json()["hour"] is None


def test_balance_endpoint_four_pillars_with_time() -> None:
    r = client.post("/five-element-balance", json={"birthdate": "2000-01-07", "birthtime": "10:00"})
    assert r.status_code == 200
    assert r.json()["pillar_count"] == 4


def test_five_element_balance_endpoint() -> None:
    r = client.post("/five-element-balance", json={"birthdate": "1990-04-15"})
    assert r.status_code == 200
    body = r.json()
    assert sum(body["scores"].values()) == body["total"]
    assert sum(body["percentages"].values()) == 100
    assert body["day_master"] == "金"  # 1990-04-15 = 庚（金）


def test_compatibility_endpoint() -> None:
    # 甲(木/2000-01-07) と 丙(火/2000-01-09) → 木生火の相生（◎）
    r = client.post(
        "/compatibility",
        json={"birthdate_a": "2000-01-07", "birthdate_b": "2000-01-09"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["type_id_a"] == "you"
    assert body["type_id_b"] == "asahi"
    assert body["relation"] == "相生"
    assert body["level"] == "◎"


def test_year_pillar_endpoint_with_time() -> None:
    # 立春当日 2024-02-04、夜（立春後）は甲辰年
    r = client.post(
        "/year-pillar", json={"birthdate": "2024-02-04", "birthtime": "20:00"}
    )
    assert r.status_code == 200
    b = r.json()
    assert b["year_stem_name"] + b["year_branch_name"] == "甲辰"

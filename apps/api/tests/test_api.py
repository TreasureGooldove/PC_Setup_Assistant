import asyncio

from fastapi.testclient import TestClient

from app.features.jobs.service import process_one
from app.main import app


def test_http_conversation_generation_flow():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        conversation = client.post("/api/conversations", json={"profile": {"budget": 8000}}).json()
        assert conversation["profile"]["budget"] == 8000
        updated = client.post(
            f"/api/conversations/{conversation['id']}/messages",
            json={"content": "预算 9000，2K 游戏，风冷"},
        ).json()
        assert updated["profile"]["budget"] == 9000
        job = client.post(f"/api/plans/generate?conversation_id={conversation['id']}").json()
        assert job["status"] == "queued"
        assert asyncio.run(process_one()) is True
        finished = client.get(f"/api/jobs/{job['id']}").json()
        assert finished["status"] == "completed"
        assert len(finished["result"]["plans"]) == 3


def test_ladder_and_game_requirement_routes():
    with TestClient(app) as client:
        ladder = client.get("/api/ladder", params={"category": "gpu"})
        assert ladder.status_code == 200
        assert ladder.json()["items"][0]["category"] == "gpu"

        games = client.get("/api/games/search", params={"query": "730"})
        assert games.status_code == 200
        assert games.json()["items"][0]["name"] == "Counter-Strike 2"

        requirements = client.get("/api/games/730/requirements")
        assert requirements.status_code == 200
        assert requirements.json()["minimum"]["memory_gb"] == 8
        assert requirements.json()["recommended"]["graphics"]


def test_ladder_filters_catalog_insights_and_demo_export_guard():
    with TestClient(app) as client:
        ladder = client.get(
            "/api/ladder",
            params={"category": "gpu", "query": "4070", "brand": "NVIDIA", "max_price": 4500},
        )
        assert ladder.status_code == 200
        assert [item["id"] for item in ladder.json()["items"]] == ["gpu-4070s"]

        catalog = client.get("/api/catalog/cpu")
        assert catalog.status_code == 200
        cpu = next(item for item in catalog.json()["items"] if item["id"] == "cpu-12600kf")
        assert cpu["benchmark_score"] > 0
        assert cpu["rank"] > 0
        assert cpu["percentile"] > 0
        assert cpu["advantages"]
        assert cpu["cautions"]
        assert cpu["url"].startswith("https://product.pconline.com.cn/")

        export = client.post("/api/plans/demo-balanced/exports")
        assert export.status_code == 409
        assert export.json()["error"]["code"] == "DEMO_PLAN_NOT_PERSISTED"

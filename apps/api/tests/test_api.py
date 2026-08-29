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

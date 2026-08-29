from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.database import init_db
from app.domain import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    PartCategory,
    ProfileUpdate,
)
from app.errors import AppError, NotFoundError, app_error_handler
from app.features.builds.catalog import fixture_parts
from app.features.builds.service import get_plan, list_plans, replace_item
from app.features.conversations.service import (
    append_message,
    create_conversation,
    get_conversation,
    update_profile,
)
from app.queue import JobQueue


class ItemUpdate(BaseModel):
    part_id: str = Field(min_length=1)
    locked: bool | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


settings = get_settings()
app = FastAPI(title="智能装机搭子 API", version="0.1.0", lifespan=lifespan)
app.add_exception_handler(AppError, app_error_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Idempotency-Key"],
)
queue = JobQueue()


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", response_model=None)
async def ready() -> dict[str, object] | JSONResponse:
    try:
        init_db()
        return {"status": "ok", "database": "ok", "provider": "fixture"}
    except Exception as exc:
        return JSONResponse(
            status_code=503, content={"status": "degraded", "detail": str(exc)[:100]}
        )


@app.post("/api/conversations", response_model=ConversationResponse)
async def create_conversation_route(body: ConversationCreate | None = None):
    body = body or ConversationCreate()
    return create_conversation(body.profile)


@app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_route(conversation_id: str):
    return get_conversation(conversation_id)


@app.post("/api/conversations/{conversation_id}/messages", response_model=ConversationResponse)
async def message_route(conversation_id: str, body: MessageCreate):
    return append_message(conversation_id, body.content)


@app.patch("/api/conversations/{conversation_id}/profile", response_model=ConversationResponse)
async def profile_route(conversation_id: str, body: ProfileUpdate):
    return update_profile(conversation_id, body.profile)


@app.post("/api/plans/generate", status_code=202)
async def generate_plans_route(
    conversation_id: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    get_conversation(conversation_id)
    key = idempotency_key or f"generate:{conversation_id}"
    return queue.enqueue(
        "generate_plans", {"conversation_id": conversation_id}, key, priority=10
    ).model_dump(mode="json")


@app.get("/api/plans")
async def list_plans_route(conversation_id: str):
    return {"plans": [plan.model_dump(mode="json") for plan in list_plans(conversation_id)]}


@app.get("/api/plans/{plan_id}")
async def get_plan_route(plan_id: str):
    return get_plan(plan_id).model_dump(mode="json")


@app.patch("/api/plans/{plan_id}/items/{slot}")
async def replace_item_route(plan_id: str, slot: PartCategory, body: ItemUpdate):
    return replace_item(plan_id, slot, body.part_id, body.locked).model_dump(mode="json")


@app.post("/api/plans/{plan_id}/refresh-offers", status_code=202)
async def refresh_offers_route(
    plan_id: str, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")
):
    get_plan(plan_id)
    key = idempotency_key or f"refresh:{plan_id}"
    return queue.enqueue("refresh_offers", {"plan_id": plan_id}, key, priority=30).model_dump(
        mode="json"
    )


@app.post("/api/plans/{plan_id}/exports", status_code=202)
async def export_route(
    plan_id: str, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")
):
    get_plan(plan_id)
    key = idempotency_key or f"export:{plan_id}"
    return queue.enqueue("export_plan", {"plan_id": plan_id}, key, priority=20).model_dump(
        mode="json"
    )


@app.get("/api/catalog/{category}")
async def catalog_route(category: PartCategory):
    return {
        "items": [
            part.model_dump(mode="json") for part in fixture_parts() if part.category == category
        ]
    }


@app.get("/api/jobs/{job_id}")
async def get_job_route(job_id: str):
    job = queue.get(job_id)
    if not job:
        raise NotFoundError("任务", job_id)
    return job.model_dump(mode="json")


@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job_route(job_id: str):
    job = queue.cancel(job_id)
    if not job:
        raise NotFoundError("任务", job_id)
    return job.model_dump(mode="json")


@app.get("/api/jobs/{job_id}/events")
async def job_events_route(job_id: str):
    if not queue.get(job_id):
        raise NotFoundError("任务", job_id)

    async def event_stream():
        last_id = 0
        while True:
            events = queue.events_since(job_id, last_id)
            for event in events:
                last_id = event["id"]
                payload = json.dumps(event, ensure_ascii=False)
                yield f"id: {last_id}\nevent: job\ndata: {payload}\n\n"
            job = queue.get(job_id)
            if job and job.status in {"completed", "cancelled", "dead_letter"}:
                break
            yield ": keep-alive\n\n"
            await asyncio.sleep(settings.job_poll_seconds)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/jobs/{job_id}/download")
async def download_job_route(job_id: str):
    job = queue.get(job_id)
    if not job:
        raise NotFoundError("任务", job_id)
    if job.status != "completed" or not job.result or not job.result.get("path"):
        raise AppError("导出尚未完成", "EXPORT_NOT_READY", 409)
    path = Path(str(job.result["path"])).resolve()
    export_root = (Path.cwd() / "data" / "exports").resolve()
    if export_root not in path.parents:
        raise AppError("导出文件路径无效", "INVALID_EXPORT_PATH", 500)
    return FileResponse(
        path,
        filename=job.result.get("file_name", path.name),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

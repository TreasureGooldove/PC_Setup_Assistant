from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.domain import PartCategory
from app.exporter import export_plan
from app.features.builds.service import get_plan, mark_refreshed, save_plans
from app.features.catalog_sync.service import sync_catalog
from app.features.conversations.service import get_conversation
from app.queue import JobQueue

THREAD_POOL_SIZE = min(8, (os.cpu_count() or 1) + 2)
PROCESS_POOL_SIZE = max(1, (os.cpu_count() or 1) // 2)


async def execute_job(queue: JobQueue, job_id: str, kind: str, payload: dict[str, Any]) -> None:
    queue.progress(job_id, 15, "读取需求")
    if kind == "generate_plans":
        conversation = get_conversation(payload["conversation_id"])
        queue.progress(job_id, 45, "计算三套方案")
        plans = save_plans(conversation.id, conversation.profile)
        queue.progress(job_id, 90, "完成兼容性检查")
        queue.complete(job_id, {"plans": [plan.model_dump(mode="json") for plan in plans]})
        return
    if kind == "refresh_offers":
        plan = mark_refreshed(payload["plan_id"])
        queue.complete(job_id, {"plan": plan.model_dump(mode="json")})
        return
    if kind == "refresh_catalog":
        category = PartCategory(payload["category"])
        queue.progress(job_id, 25, "连接公开候选目录")
        result = await sync_catalog(category)
        queue.progress(job_id, 85, "写入本地候选缓存")
        queue.complete(job_id, result)
        return
    if kind == "export_plan":
        plan = get_plan(payload["plan_id"])
        output_dir = Path.cwd() / "data" / "exports"
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE, thread_name_prefix="export") as pool:
            path = await loop.run_in_executor(pool, export_plan, plan, output_dir, job_id)
        queue.complete(job_id, {"path": path, "file_name": Path(path).name})
        return
    raise ValueError(f"未知任务类型：{kind}")


async def process_one(queue: JobQueue | None = None) -> bool:
    queue = queue or JobQueue()
    claimed = queue.claim()
    if not claimed:
        return False
    job, payload = claimed
    try:
        await execute_job(queue, job.id, job.kind, payload)
    except Exception as exc:  # 任务边界统一转换为可重试状态
        queue.fail(job.id, str(exc)[:500])
    return True

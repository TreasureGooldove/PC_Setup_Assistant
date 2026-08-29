from __future__ import annotations

import asyncio

from app.config import get_settings
from app.database import init_db
from app.features.jobs.service import process_one
from app.queue import JobQueue


async def run() -> None:
    init_db()
    queue = JobQueue()
    settings = get_settings()
    print("worker started")
    try:
        while True:
            processed = await process_one(queue)
            if not processed:
                await asyncio.sleep(settings.job_poll_seconds)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("worker stopped")


if __name__ == "__main__":
    asyncio.run(run())

import asyncio

from app.features.jobs.service import process_one
from app.queue import JobQueue


def test_queue_is_idempotent_and_processes_export(tmp_path, monkeypatch):
    queue = JobQueue()
    first = queue.enqueue("unknown", {"value": 1}, "same-key")
    second = queue.enqueue("unknown", {"value": 2}, "same-key")
    assert first.id == second.id

    queue.fail(first.id, "temporary")
    assert queue.get(first.id).status == "queued"


def test_queue_generate_job_completion():
    from app.domain import NeedProfile
    from app.features.conversations.service import create_conversation

    conversation = create_conversation(NeedProfile(budget=8000))
    queue = JobQueue()
    job = queue.enqueue("generate_plans", {"conversation_id": conversation.id}, "generate-test")
    assert asyncio.run(process_one(queue)) is True
    assert queue.get(job.id).status == "completed"

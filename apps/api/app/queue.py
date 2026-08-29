from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select, update

from app.config import get_settings
from app.database import JobEventRecord, JobRecord, SessionLocal, json_dump, json_load
from app.domain import Job
from app.errors import QueueFullError


def _to_job(record: JobRecord) -> Job:
    return Job(
        id=record.id,
        kind=record.kind,
        status=record.status,
        progress=record.progress,
        message=record.message,
        result=json_load(record.result_json, None),
        error=record.error,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


class JobQueue:
    max_size = 100
    max_attempts = 3

    def enqueue(
        self, kind: str, payload: dict[str, Any], idempotency_key: str, priority: int = 50
    ) -> Job:
        with SessionLocal() as session:
            existing = session.scalar(
                select(JobRecord).where(JobRecord.idempotency_key == idempotency_key)
            )
            if existing:
                return _to_job(existing)
            current_size = (
                session.scalar(
                    select(func.count())
                    .select_from(JobRecord)
                    .where(JobRecord.status.in_(["queued", "running"]))
                )
                or 0
            )
            if current_size >= self.max_size:
                raise QueueFullError()
            now = datetime.now(UTC)
            record = JobRecord(
                id=str(uuid4()),
                kind=kind,
                status="queued",
                priority=priority,
                payload_json=json_dump(payload),
                idempotency_key=idempotency_key,
                progress=0,
                message="排队中",
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.flush()
            session.add(
                JobEventRecord(job_id=record.id, status="queued", progress=0, message="排队中")
            )
            session.commit()
            return _to_job(record)

    def get(self, job_id: str) -> Job | None:
        with SessionLocal() as session:
            record = session.get(JobRecord, job_id)
            return _to_job(record) if record else None

    def claim(self) -> tuple[Job, dict[str, Any]] | None:
        settings = get_settings()
        now = datetime.now(UTC)
        with SessionLocal() as session:
            session.execute(
                update(JobRecord)
                .where(JobRecord.status == "running", JobRecord.lease_until < now)
                .values(status="queued", message="租约已恢复", updated_at=now)
            )
            candidate = session.scalar(
                select(JobRecord)
                .where(JobRecord.status == "queued")
                .order_by(JobRecord.priority, JobRecord.created_at)
                .limit(1)
            )
            if not candidate:
                session.commit()
                return None
            candidate.status = "running"
            candidate.attempts += 1
            candidate.lease_until = now + timedelta(seconds=settings.job_lease_seconds)
            candidate.message = "执行中"
            candidate.updated_at = now
            session.add(
                JobEventRecord(job_id=candidate.id, status="running", progress=0, message="执行中")
            )
            payload = json_load(candidate.payload_json, {})
            job = _to_job(candidate)
            session.commit()
            return job, payload

    def progress(self, job_id: str, value: int, message: str) -> None:
        now = datetime.now(UTC)
        with SessionLocal() as session:
            record = session.get(JobRecord, job_id)
            if not record:
                return
            record.progress = max(0, min(100, value))
            record.message = message
            record.updated_at = now
            session.add(
                JobEventRecord(
                    job_id=job_id, status=record.status, progress=record.progress, message=message
                )
            )
            session.commit()

    def complete(self, job_id: str, result: dict[str, Any]) -> None:
        self._finish(job_id, "completed", 100, "已完成", result=result)

    def fail(self, job_id: str, error: str) -> None:
        with SessionLocal() as session:
            record = session.get(JobRecord, job_id)
            if not record:
                return
            retryable = record.attempts < self.max_attempts
            status = "queued" if retryable else "dead_letter"
            message = "失败，准备重试" if retryable else "失败，已进入死信"
            self._update_record(record, status, record.progress, message, error, session)
            session.commit()

    def cancel(self, job_id: str) -> Job | None:
        with SessionLocal() as session:
            record = session.get(JobRecord, job_id)
            if not record:
                return None
            if record.status in {"queued", "running"}:
                self._update_record(record, "cancelled", record.progress, "已取消", None, session)
            session.commit()
            return _to_job(record)

    def events_since(self, job_id: str, after_id: int = 0) -> list[dict[str, Any]]:
        with SessionLocal() as session:
            rows = session.scalars(
                select(JobEventRecord)
                .where(JobEventRecord.job_id == job_id, JobEventRecord.id > after_id)
                .order_by(JobEventRecord.id)
            ).all()
            return [
                {
                    "id": row.id,
                    "status": row.status,
                    "progress": row.progress,
                    "message": row.message,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]

    @staticmethod
    def _update_record(
        record: JobRecord, status: str, progress: int, message: str, error: str | None, session: Any
    ) -> None:
        now = datetime.now(UTC)
        record.status = status
        record.progress = progress
        record.message = message
        record.error = error
        record.lease_until = None
        record.updated_at = now
        session.add(
            JobEventRecord(job_id=record.id, status=status, progress=progress, message=message)
        )

    def _finish(
        self,
        job_id: str,
        status: str,
        progress: int,
        message: str,
        result: dict[str, Any] | None = None,
    ) -> None:
        with SessionLocal() as session:
            record = session.get(JobRecord, job_id)
            if not record:
                return
            self._update_record(record, status, progress, message, None, session)
            record.result_json = json_dump(result) if result is not None else None
            session.commit()

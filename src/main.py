from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

MAX_TASKS = int(os.getenv("MAX_TASKS", "1000"))
QUEUE_CAPACITY = int(os.getenv("QUEUE_CAPACITY", "256"))
WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "4"))
MAX_PAYLOAD_BYTES = 16 * 1024

if not 1 <= MAX_TASKS <= 100_000:
    raise RuntimeError("MAX_TASKS must be between 1 and 100000")
if not 1 <= QUEUE_CAPACITY <= 10_000:
    raise RuntimeError("QUEUE_CAPACITY must be between 1 and 10000")
if not 1 <= WORKER_CONCURRENCY <= 64:
    raise RuntimeError("WORKER_CONCURRENCY must be between 1 and 64")

TaskOperation = Literal["echo", "uppercase", "sum"]
TaskState = Literal["queued", "running", "succeeded", "failed"]


class TaskRequest(BaseModel):
    operation: TaskOperation
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskRecord(BaseModel):
    task_id: str
    operation: TaskOperation
    state: TaskState
    created_at: datetime
    updated_at: datetime
    result: Any | None = None
    error: str | None = None


class TaskStore:
    def __init__(self, max_tasks: int) -> None:
        self.max_tasks = max_tasks
        self.records: dict[str, TaskRecord] = {}
        self.order: list[str] = []
        self.lock = asyncio.Lock()

    async def create(self, operation: TaskOperation) -> TaskRecord:
        now = datetime.now(UTC)
        record = TaskRecord(
            task_id=str(uuid4()),
            operation=operation,
            state="queued",
            created_at=now,
            updated_at=now,
        )
        async with self.lock:
            while len(self.order) >= self.max_tasks:
                oldest = self.order.pop(0)
                self.records.pop(oldest, None)
            self.records[record.task_id] = record
            self.order.append(record.task_id)
        return record

    async def get(self, task_id: str) -> TaskRecord | None:
        async with self.lock:
            return self.records.get(task_id)

    async def update(self, task_id: str, **changes: Any) -> None:
        async with self.lock:
            current = self.records[task_id]
            self.records[task_id] = current.model_copy(
                update={**changes, "updated_at": datetime.now(UTC)}
            )

    async def count(self) -> int:
        async with self.lock:
            return len(self.records)


async def execute(operation: TaskOperation, payload: dict[str, Any]) -> Any:
    await asyncio.sleep(0)
    if operation == "echo":
        return payload
    if operation == "uppercase":
        text = payload.get("text")
        if not isinstance(text, str) or not 1 <= len(text) <= 4_000:
            raise ValueError("uppercase requires text with 1-4000 characters")
        return {"text": text.upper()}
    if operation == "sum":
        values = payload.get("values")
        if not isinstance(values, list) or not 1 <= len(values) <= 1_000:
            raise ValueError("sum requires values with 1-1000 numbers")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
            raise ValueError("sum values must all be numbers")
        total = sum(values)
        if not -1e15 <= total <= 1e15:
            raise ValueError("sum result is outside the supported range")
        return {"sum": total}
    raise ValueError("unsupported operation")


store = TaskStore(MAX_TASKS)
queue: asyncio.Queue[tuple[str, TaskRequest]] = asyncio.Queue(maxsize=QUEUE_CAPACITY)


async def worker() -> None:
    while True:
        task_id, request = await queue.get()
        try:
            await store.update(task_id, state="running")
            try:
                result = await execute(request.operation, request.payload)
            except (ValueError, TypeError) as exc:
                await store.update(task_id, state="failed", error=str(exc))
            else:
                await store.update(task_id, state="succeeded", result=result)
        finally:
            queue.task_done()


@asynccontextmanager
async def lifespan(_: FastAPI):
    workers = [asyncio.create_task(worker()) for _ in range(WORKER_CONCURRENCY)]
    try:
        yield
    finally:
        for task in workers:
            task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)


app = FastAPI(title="Sky Async Worker", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
async def health() -> dict[str, object]:
    return {"status": "ok", "service": "sky-async-worker"}


@app.get("/readyz")
async def ready() -> dict[str, object]:
    return {
        "ready": True,
        "queued": queue.qsize(),
        "queueCapacity": QUEUE_CAPACITY,
        "retainedTasks": await store.count(),
    }


@app.post("/api/v1/tasks", status_code=status.HTTP_202_ACCEPTED)
async def create_task(request: TaskRequest) -> dict[str, str]:
    payload_size = len(json.dumps(request.payload, separators=(",", ":"), ensure_ascii=False).encode())
    if payload_size > MAX_PAYLOAD_BYTES:
        raise HTTPException(status_code=413, detail="task payload exceeds 16 KiB")
    if queue.full():
        raise HTTPException(status_code=503, detail="task queue is full")
    record = await store.create(request.operation)
    queue.put_nowait((record.task_id, request))
    return {"task_id": record.task_id, "state": record.state}


@app.get("/api/v1/tasks/{task_id}", response_model=TaskRecord)
async def get_task(task_id: str) -> TaskRecord:
    record = await store.get(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail="task not found")
    return record

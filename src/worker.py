import asyncio
from dataclasses import dataclass
from typing import Callable, Any, List
from collections import deque

@dataclass
class Job:
    id: str
    fn: Callable
    args: tuple
    result: Any = None
    error: str = None
    done: bool = False

class AsyncWorkerPool:
    def __init__(self, concurrency: int = 4):
        self.concurrency = concurrency
        self.queue: deque = deque()
        self.results: dict = {}

    def enqueue(self, job: Job):
        self.queue.append(job)
        self.results[job.id] = job

    async def _run_job(self, job: Job):
        try:
            if asyncio.iscoroutinefunction(job.fn):
                job.result = await job.fn(*job.args)
            else:
                loop = asyncio.get_event_loop()
                job.result = await loop.run_in_executor(None, job.fn, *job.args)
        except Exception as e:
            job.error = str(e)
        finally:
            job.done = True

    async def run_all(self):
        sem = asyncio.Semaphore(self.concurrency)
        async def bounded(job):
            async with sem:
                await self._run_job(job)
        tasks = [bounded(j) for j in self.queue]
        await asyncio.gather(*tasks)

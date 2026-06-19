import asyncio
from src.worker import Job, AsyncWorkerPool

def square(x):
    return x * x

async def async_double(x):
    await asyncio.sleep(0)
    return x * 2

def test_sync_jobs():
    pool = AsyncWorkerPool(concurrency=2)
    pool.enqueue(Job(id="j1", fn=square, args=(4,)))
    pool.enqueue(Job(id="j2", fn=square, args=(5,)))
    asyncio.run(pool.run_all())
    assert pool.results["j1"].result == 16
    assert pool.results["j2"].result == 25

def test_async_jobs():
    pool = AsyncWorkerPool(concurrency=2)
    pool.enqueue(Job(id="a1", fn=async_double, args=(7,)))
    asyncio.run(pool.run_all())
    assert pool.results["a1"].result == 14

def test_error_handling():
    def bad_fn():
        raise ValueError("boom")
    pool = AsyncWorkerPool()
    pool.enqueue(Job(id="e1", fn=bad_fn, args=()))
    asyncio.run(pool.run_all())
    assert pool.results["e1"].error == "boom"
    assert pool.results["e1"].done is True

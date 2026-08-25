# Sky Async Worker

**Status: engineering beta.** A bounded Python/FastAPI asyncio task service with explicit built-in operations and observable task lifecycle state.

## Implemented behavior

- bounded in-memory task retention and queue capacity
- configurable worker concurrency
- UUID task identifiers
- lifecycle states: `queued`, `running`, `succeeded`, `failed`
- allow-listed operations only: `echo`, `uppercase`, and numeric `sum`
- payload-size limits and per-operation validation
- health/readiness endpoints with queue/task counts
- real asynchronous workers started through the FastAPI lifespan
- tests for successful execution, validation failure, unsupported operations, oversized payloads, readiness, and missing tasks
- CI gates for compile, Ruff, pytest, dependency audit, Docker build, non-root runtime, and container health smoke testing

## Run

```bash
python -m pip install -r requirements-dev.txt
pytest -q
uvicorn src.main:app --host 127.0.0.1 --port 8080
```

Create a task:

```bash
curl -X POST http://127.0.0.1:8080/api/v1/tasks \
  -H 'content-type: application/json' \
  -d '{"operation":"sum","payload":{"values":[1,2,3]}}'
```

Read the returned task ID:

```bash
curl http://127.0.0.1:8080/api/v1/tasks/<task-id>
```

## Configuration

- `MAX_TASKS` defaults to `1000`
- `QUEUE_CAPACITY` defaults to `256`
- `WORKER_CONCURRENCY` defaults to `4`

Invalid configuration fails closed during startup.

## SKYCOIN4444 integration

The service can provide a small asynchronous execution boundary for approved deterministic background operations in development or single-node deployments. Larger ecosystem jobs should integrate through explicit operation adapters rather than allowing requests to supply Python modules, shell commands, URLs, or executable code.

## Explicit limitations

Task and queue state are process-local and disappear on restart. This repository is not Celery, Temporal, Sidekiq, a durable queue, a distributed worker fleet, or an arbitrary-code runner. It does not provide persistence, retries, scheduled jobs, exactly-once delivery, authentication, authorization, tenant isolation, distributed locking, HA, or production deployment.

See `SECURITY.md` and `CHANGELOG.md` for boundaries and productization history.

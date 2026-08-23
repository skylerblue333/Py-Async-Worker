# Ecosystem Integration

**Role:** asynchronous background job execution.

**Foundation:** Celery + Redis. This repository owns task definitions; the platform owns business contracts.

**Consumes:** durable task payloads from APIs/events.

**Provides:** retried asynchronous execution and result state.

**Production requirements:** idempotent tasks, dead-letter/error handling, bounded retries, telemetry, queue isolation, and explicit task versioning.

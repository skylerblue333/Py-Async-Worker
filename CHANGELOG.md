# Changelog

## 0.1.0 - 2026-08-24

- Replace the pending-only task stub with real bounded asyncio workers.
- Add queued/running/succeeded/failed lifecycle state and UUID task IDs.
- Add allow-listed echo, uppercase, and sum operations with input limits.
- Add queue/task capacity and worker-concurrency configuration bounds.
- Add health/readiness endpoints and deterministic API tests.
- Modernize Python dependencies and CI with Ruff, pytest, pip-audit, Docker, non-root, and runtime smoke gates.
- Document explicit security and durability limitations.

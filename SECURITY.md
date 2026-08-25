# Security Policy

Sky Async Worker is an engineering-beta task-processing service, not a production trust boundary.

The API accepts only allow-listed operations. Requests cannot provide shell commands, Python module paths, executable expressions, or arbitrary plugin names. Payload size, task retention, queue depth, worker concurrency, and operation-specific inputs are bounded. The container runs as a non-root user and CI audits runtime dependencies.

This repository does not provide authentication, authorization, tenant isolation, durable audit logs, encrypted persistence, distributed rate limiting, secrets management, sandboxed code execution, or production network controls. Put the service behind an authenticated gateway before exposing it outside a trusted environment.

Report vulnerabilities privately through GitHub security reporting when available. Do not post credentials, private task data, or working exploit details in public issues.

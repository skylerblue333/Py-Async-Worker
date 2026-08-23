"""Celery-backed asynchronous worker entry point."""
import os
from celery import Celery

broker = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
app = Celery("skycoin_worker", broker=broker, backend=os.getenv("CELERY_RESULT_BACKEND", broker))

@app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process(payload: dict) -> dict:
    return {"status": "processed", "payload": payload}

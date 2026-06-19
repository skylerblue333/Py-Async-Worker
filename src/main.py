from fastapi import FastAPI
app = FastAPI(title="Async Worker Pool")

@app.get("/health")
def health():
    return {"status": "ok", "service": "async-worker"}

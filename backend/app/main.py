from fastapi import FastAPI
from app.db import engine
from sqlalchemy import text

app = FastAPI(title="Second Brain API")

@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "database" : "connected"}
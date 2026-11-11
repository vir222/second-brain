from fastapi import FastAPI
from app.db import engine
from sqlalchemy import text
from app.routers import auth, users, notebooks


app = FastAPI(title="Second Brain API")
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(notebooks.router)

@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "database" : "connected"}
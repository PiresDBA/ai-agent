from fastapi import FastAPI
from pydantic import BaseModel
from engine.pipeline import run_pipeline

app = FastAPI()


# 🧠 DEFINE O SCHEMA (ESSENCIAL)
class RunRequest(BaseModel):
    prompt: str
    user_id: str | None = None


@app.post("/run")
def run(payload: RunRequest):
    return run_pipeline(payload.prompt, payload.user_id)
@app.get("/")
def home():
    return {
        "status": "Antigravity v6 running",
        "message": "Use /docs to test API"
    }
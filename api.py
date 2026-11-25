"""FastAPI wrapper around the shield. Start: uvicorn api:app --reload   then open /docs"""
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from shield.pipeline import run

app = FastAPI(title="PromptShield", description="Prompt-injection firewall for an LLM chatbot")


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=5000)
    shield_on: bool = True


class ChatResponse(BaseModel):
    verdict: str
    reply: str
    blocked_by: Optional[str]
    risk_score: Optional[float]
    attack_type: Optional[str]
    masked_entities: list
    latency_ms: dict


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    return run(req.message, req.shield_on)

"""FastAPI wrapper around the shield. Start: uvicorn api:app --reload   then open /docs"""
import os
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
    # Clients may only switch the shield off when the operator allows it (local demos).
    shield_on = req.shield_on or os.getenv("ALLOW_SHIELD_OFF") != "1"
    return run(req.message, shield_on)

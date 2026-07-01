from fastapi import FastAPI
from models.schemas import ChatRequest
from services.intent_router import detect_intent
from services.recommendation_agent import (
    build_recommendations,
    refine_recommendations,
    confirm_recommendations
)
from services.comparison_agent import compare_assessments
from services.refusal_agent import refuse


app = FastAPI(title="SHL Assessment Recommender")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):
    intent = detect_intent(request.messages)

    if intent == "refuse":
        return refuse()

    if intent == "clarify":
        return {
            "reply": "Sure. What role are you hiring for, and what skills, seniority level, or traits should the assessment measure?",
            "recommendations": [],
            "end_of_conversation": False
        }

    if intent == "compare":
        return compare_assessments(request.messages)

    if intent == "refine":
        return refine_recommendations(request.messages)

    if intent == "confirm":
        return confirm_recommendations(request.messages)

    return build_recommendations(request.messages)
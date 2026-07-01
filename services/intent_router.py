OFF_TOPIC_WORDS = [
    "salary", "legal", "law", "visa", "resume", "interview tips",
    "hiring advice", "job description write", "contract", "hipaa required"
]

COMPARE_WORDS = [
    "difference", "compare", "vs", "versus", "different from"
]

CONFIRM_WORDS = [
    "perfect", "thanks", "thank you", "confirmed", "that works",
    "good", "that's good", "ok", "okay"
]

REFINE_WORDS = [
    "add", "remove", "drop", "replace", "actually", "include",
    "exclude", "instead"
]


def latest_user_message(messages):
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content
    return ""


def conversation_text(messages):
    return "\n".join([f"{m.role}: {m.content}" for m in messages])


def detect_intent(messages):
    latest = latest_user_message(messages).lower()

    hiring_keywords = [
        "hire", "hiring", "assessment", "assessments", "test", "tests",
        "candidate", "role", "developer", "engineer", "manager",
        "sales", "skills", "java", "spring", "sql", "python",
        "frontend", "backend", "graduate", "senior", "mid-level",
        "entry-level"
    ]

    if not any(word in latest for word in hiring_keywords):
        return "refuse"

    if any(word in latest for word in OFF_TOPIC_WORDS):
        return "refuse"

    if any(word in latest for word in COMPARE_WORDS):
        return "compare"

    if any(word in latest for word in CONFIRM_WORDS):
        return "confirm"

    if any(word in latest for word in REFINE_WORDS):
        return "refine"

    vague_phrases = [
        "i need an assessment",
        "need assessment",
        "suggest assessment",
        "recommend assessment",
        "need tests",
        "tests for hiring",
        "we need a solution",
        "hiring someone"
    ]

    if len(latest.split()) <= 6 or any(v in latest for v in vague_phrases):
        return "clarify"

    return "recommend"
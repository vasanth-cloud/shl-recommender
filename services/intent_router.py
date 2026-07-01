OFF_TOPIC_WORDS = [
    "salary", "compensation", "legal", "law", "visa", "resume",
    "interview tips", "hiring advice", "write a job description",
    "contract", "prompt injection", "ignore previous",
    "system prompt", "jailbreak"
]

LEGAL_ADVICE_WORDS = [
    "legally required", "legal requirement", "required under hipaa",
    "satisfy that requirement", "satisfies that requirement",
    "regulatory obligation", "compliance obligation"
]

COMPARE_WORDS = [
    "difference", "compare", " vs ", "versus", "different from", "which is better"
]

CONFIRM_WORDS = [
    "perfect", "thanks", "thank you", "confirmed", "that works",
    "looks good", "that's good", "ok", "okay", "final list",
    "locking it in", "lock it in", "covers it", "clear."
]

REFINE_WORDS = [
    "add", "remove", "drop", "replace", "actually", "include",
    "exclude", "instead", "also", "more", "less", "change"
]

HIRING_KEYWORDS = [
    "hire", "hiring", "assessment", "assessments", "test", "tests",
    "candidate", "role", "developer", "engineer", "manager", "analyst",
    "sales", "support", "service", "skills", "java", "spring", "sql",
    "python", "frontend", "backend", "graduate", "senior", "mid-level",
    "entry-level", "personality", "cognitive", "aptitude", "reasoning",
    "opq", "gsa", "verify", "excel", "solution", "leadership",
    "reskill", "re-skill", "talent audit", "contact centre",
    "contact center", "healthcare", "hipaa", "admin", "safety",
    "finance", "financial", "rust", "full-stack", "full stack"
]

CONTEXT_KEYWORDS = [
    "developer", "engineer", "manager", "analyst", "sales", "support",
    "service", "java", "python", "sql", "excel", "frontend", "backend",
    "spring", "react", "angular", "aws", "graduate", "entry", "senior",
    "mid-level", "mid level", "stakeholder", "communication", "personality",
    "cognitive", "aptitude", "reasoning", "leadership", "solution",
    "contact centre", "contact center", "healthcare", "safety",
    "finance", "financial", "reskill", "re-skill", "talent audit"
]


def latest_user_message(messages):
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content
    return ""


def user_text(messages):
    return "\n".join(m.content for m in messages if m.role == "user")


def conversation_text(messages):
    return "\n".join([f"{m.role}: {m.content}" for m in messages])


def has_prior_recommendation(messages):
    return any(
        m.role == "assistant"
        and (
            "shortlist" in m.content.lower()
            or "recommend" in m.content.lower()
            or "here are" in m.content.lower()
            or "assessment" in m.content.lower()
        )
        for m in messages
    )


def is_vague(text):
    lowered = text.lower().strip()
    vague_phrases = [
        "i need an assessment",
        "need assessment",
        "suggest assessment",
        "recommend assessment",
        "need tests",
        "tests for hiring",
        "we need a solution",
        "hiring someone",
        "help me choose",
    ]

    if any(v in lowered for v in vague_phrases) and not any(k in lowered for k in CONTEXT_KEYWORDS):
        return True

    return len(lowered.split()) <= 6 and not any(k in lowered for k in CONTEXT_KEYWORDS)


def detect_intent(messages):
    latest = latest_user_message(messages).lower()
    all_user = user_text(messages).lower()

    if any(word in latest for word in OFF_TOPIC_WORDS):
        return "refuse"

    if any(word in latest for word in LEGAL_ADVICE_WORDS):
        return "refuse"

    if any(word in latest for word in COMPARE_WORDS):
        return "compare"

    if has_prior_recommendation(messages) and any(word in latest for word in CONFIRM_WORDS):
        return "confirm"

    if has_prior_recommendation(messages) and any(word in latest for word in REFINE_WORDS):
        return "refine"

    if not any(word in all_user for word in HIRING_KEYWORDS):
        return "refuse"

    if is_vague(all_user):
        return "clarify"

    return "recommend"

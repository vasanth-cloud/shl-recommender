from services.retriever import search_catalog
from services.intent_router import conversation_text


TECH_SKILLS = [
    "java", "spring", "sql", "aws", "docker", "angular",
    "python", "react", "linux", "networking", "excel", "word"
]


def extract_skills(text: str):
    text = text.lower()
    return [skill for skill in TECH_SKILLS if skill in text]


def item_matches_skill(item, skills):
    searchable = (
        item["name"] + " " +
        item["description"] + " " +
        " ".join(item["keys"])
    ).lower()

    for skill in skills:
        if skill in searchable:
            return True

    return False


def format_recommendations(items):
    return [
        {
            "name": item["name"],
            "url": item["url"],
            "test_type": item["test_type"]
        }
        for item in items[:10]
    ]


def build_recommendations(messages):
    query = conversation_text(messages)
    skills = extract_skills(query)

    results = search_catalog(query, top_k=30)

    if skills:
        filtered = [
            item for item in results
            if item_matches_skill(item, skills)
        ]
    else:
        filtered = results

    recommendations = format_recommendations(filtered)

    return {
        "reply": "Based on your hiring context, here are the SHL assessments that best match the role.",
        "recommendations": recommendations,
        "end_of_conversation": False
    }


def refine_recommendations(messages):
    return build_recommendations(messages)


def confirm_recommendations(messages):
    data = build_recommendations(messages)
    data["reply"] = "Confirmed. Here is the final shortlist."
    data["end_of_conversation"] = True
    return data
from services.retriever import search_catalog


def compare_assessments(messages):
    latest = ""

    for msg in reversed(messages):
        if msg.role == "user":
            latest = msg.content
            break

    results = search_catalog(latest, top_k=5)

    if len(results) < 2:
        return {
            "reply": "I can compare SHL assessments only when I can identify the catalog items. Please mention the assessment names clearly.",
            "recommendations": [],
            "end_of_conversation": False
        }

    a = results[0]
    b = results[1]

    reply = (
        f"{a['name']} is mainly related to {', '.join(a['keys'])}. "
        f"{a['description']} "
        f"\n\n{b['name']} is mainly related to {', '.join(b['keys'])}. "
        f"{b['description']}"
    )

    return {
        "reply": reply,
        "recommendations": [],
        "end_of_conversation": False
    }
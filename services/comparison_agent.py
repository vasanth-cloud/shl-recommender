from services.intent_router import latest_user_message
from services.retriever import find_catalog_items


def describe(item):
    parts = [
        f"{item['name']} ({item['test_type']})",
        f"catalog type: {', '.join(item['keys']) or 'not specified'}",
    ]

    if item.get("job_levels"):
        parts.append(f"job levels: {', '.join(item['job_levels'][:5])}")
    if item.get("duration"):
        parts.append(f"duration: {item['duration']}")

    return "; ".join(parts) + f". {item['description']}"


def compare_assessments(messages):
    latest = latest_user_message(messages)
    results = find_catalog_items(latest, limit=4)

    if len(results) < 2:
        return {
            "reply": (
                "I can compare SHL assessments only when I can identify at least "
                "two catalog items. Please mention the assessment names clearly."
            ),
            "recommendations": [],
            "end_of_conversation": False
        }

    first, second = results[0], results[1]
    reply = (
        f"{describe(first)}\n\n"
        f"{describe(second)}\n\n"
        "In short, choose the first when its catalog description and type match "
        "the capability you need more closely; choose the second when those "
        "catalog attributes better match the role."
    )

    return {
        "reply": reply,
        "recommendations": [],
        "end_of_conversation": False
    }

from services.intent_router import user_text
from services.llm_ranker import rerank_with_llm
from services.retriever import catalog, is_recommendable, search_catalog


DEFAULT_RECOMMENDATIONS = [
    "Verify - G+",
    "SHL Verify Interactive G+",
    "Occupational Personality Questionnaire OPQ32r",
    "Global Skills Assessment",
]


def format_recommendations(items):
    formatted = []
    seen_urls = set()

    for item in items:
        if item["url"] in seen_urls:
            continue
        seen_urls.add(item["url"])
        formatted.append({
            "name": item["name"],
            "url": item["url"],
            "test_type": item["test_type"]
        })
        if len(formatted) == 10:
            break

    return formatted


def fallback_items():
    by_name = {item["name"]: item for item in catalog}
    return [
        by_name[name]
        for name in DEFAULT_RECOMMENDATIONS
        if name in by_name and is_recommendable(by_name[name])
    ]


def build_recommendations(messages):
    query = user_text(messages)
    results = search_catalog(query, top_k=50, recommendable_only=True)

    if not results:
        results = fallback_items()

    try:
        llm_result = rerank_with_llm(query, results)
    except Exception:
        llm_result = None
    if llm_result:
        recommendations = format_recommendations(llm_result["items"])
        return {
            "reply": llm_result["reply"],
            "recommendations": recommendations,
            "end_of_conversation": False
        }

    recommendations = format_recommendations(results)

    return {
        "reply": (
            f"Based on the SHL catalog, here are {len(recommendations)} "
            "assessments that best match the role and constraints you shared."
        ),
        "recommendations": recommendations,
        "end_of_conversation": False
    }


def refine_recommendations(messages):
    data = build_recommendations(messages)
    data["reply"] = (
        "Updated the shortlist using your latest constraint while staying within "
        "the SHL product catalog."
    )
    return data


def confirm_recommendations(messages):
    data = build_recommendations(messages)
    data["reply"] = "Confirmed. Here is the final SHL assessment shortlist."
    data["end_of_conversation"] = True
    return data

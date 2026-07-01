import re

from services.intent_router import user_text
from services.llm_ranker import rerank_with_llm
from services.retriever import catalog, is_recommendable, search_catalog


PROGRAMMING_LANGUAGE_TERMS = {
    "java": ["java"],
    "python": ["python"],
    "javascript": ["javascript", "react", "angular", "html/css", "html5", "css3"],
    "c#": ["c#", "c sharp", ".net", "asp.net"],
    "c++": ["c++"],
    "php": ["php"],
    "ruby": ["ruby"],
    "go": ["golang", " go "],
    "swift": ["swift"],
}

DEFAULT_RECOMMENDATIONS = [
    "Verify - G+",
    "SHL Verify Interactive G+",
    "Occupational Personality Questionnaire OPQ32r",
    "Global Skills Assessment",
]


def mentioned_languages(query):
    lowered = f" {query.lower()} "
    mentioned = set()

    for language, terms in PROGRAMMING_LANGUAGE_TERMS.items():
        for term in terms:
            clean_term = term.strip()
            if clean_term in {".net", "asp.net", "html/css", "html5", "css3"}:
                pattern = re_escape(term)
            else:
                pattern = rf"\b{re_escape(clean_term)}\b"
            if re.search(pattern, lowered):
                mentioned.add(language)
                break

    return mentioned


def re_escape(value):
    return re.escape(value)


def item_mentions_language(item, language):
    text = f" {item['name']} {item.get('description', '')} ".lower()

    for term in PROGRAMMING_LANGUAGE_TERMS[language]:
        clean_term = term.strip()
        if clean_term in {".net", "asp.net", "html/css", "html5", "css3"}:
            pattern = re_escape(clean_term)
        else:
            pattern = rf"\b{re_escape(clean_term)}\b"
        if re.search(pattern, text):
            return True

    return False


def enforce_language_constraints(query, items):
    languages = mentioned_languages(query)
    if not languages:
        return items

    filtered = []
    for item in items:
        item_languages = {
            language
            for language in PROGRAMMING_LANGUAGE_TERMS
            if item_mentions_language(item, language)
        }
        if item_languages and item_languages.isdisjoint(languages):
            continue
        filtered.append(item)

    return filtered or items


def enforce_role_constraints(query, items):
    lowered = query.lower()
    developer_context = any(
        term in lowered
        for term in ["developer", "engineer", "software", "backend", "frontend", "programmer"]
    )
    service_context = any(term in lowered for term in ["sales", "customer", "contact center", "call center"])

    if not developer_context or service_context:
        return items

    blocked_terms = ["sales", "customer service", "contact center", "call simulation"]
    filtered = [
        item for item in items
        if not any(term in item["name"].lower() for term in blocked_terms)
    ]

    return filtered or items


def apply_hard_constraints(query, items):
    return enforce_role_constraints(
        query,
        enforce_language_constraints(query, items)
    )


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
    results = apply_hard_constraints(query, results)

    if not results:
        results = fallback_items()

    try:
        llm_result = rerank_with_llm(query, results)
    except Exception:
        llm_result = None
    if llm_result:
        llm_items = llm_result["items"] + [
            item for item in results
            if item["url"] not in {selected["url"] for selected in llm_result["items"]}
        ]
        recommendations = format_recommendations(
            apply_hard_constraints(query, llm_items)
        )
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

import re

from services.intent_router import latest_user_message, user_text
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

FRESH_QUERY_MARKERS = [
    "hire", "hiring", "need assessment", "need tests", "looking for",
    "recruiting", "candidate for", "role for", "job description"
]

REFINEMENT_MARKERS = [
    "actually", "also", "add", "remove", "include", "exclude",
    "instead", "change", "make it", "what about"
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


def enforce_exclusions(query, items):
    lowered = query.lower()
    blocked_name_terms = []

    if re.search(r"\b(drop|remove|exclude|without)\s+(the\s+)?(opq|opq32r|personality)\b", lowered):
        blocked_name_terms.extend(["opq", "occupational personality"])
    if re.search(r"\b(drop|remove|exclude|without)\s+(the\s+)?rest\b", lowered):
        blocked_name_terms.append("rest")
    if re.search(r"\b(drop|remove|exclude|without)\s+(the\s+)?verify\b", lowered):
        blocked_name_terms.append("verify")
    if re.search(r"\b(drop|remove|exclude|without)\s+(the\s+)?g\+\b", lowered):
        blocked_name_terms.append("g+")

    if not blocked_name_terms:
        return items

    filtered = [
        item for item in items
        if not any(term in item["name"].lower() for term in blocked_name_terms)
    ]

    return filtered or items


def apply_hard_constraints(query, items):
    return enforce_exclusions(
        query,
        enforce_role_constraints(
            query,
            enforce_language_constraints(query, items)
        )
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


def recommendation_query(messages):
    latest = latest_user_message(messages).strip()
    lowered = latest.lower()

    if (
        any(marker in lowered for marker in FRESH_QUERY_MARKERS)
        and not any(marker in lowered for marker in REFINEMENT_MARKERS)
    ):
        return latest

    return user_text(messages)


def build_recommendations(messages):
    query = recommendation_query(messages)
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

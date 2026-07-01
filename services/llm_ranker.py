import json
import os
import re

import httpx


DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_BASE_URL = "https://api.openai.com/v1"


def llm_configured():
    return bool(os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))


def compact_item(index, item):
    description = re.sub(r"\s+", " ", item.get("description", "")).strip()
    if len(description) > 360:
        description = description[:357] + "..."

    return {
        "id": index,
        "name": item["name"],
        "test_type": item["test_type"],
        "keys": item.get("keys", []),
        "job_levels": item.get("job_levels", []),
        "duration": item.get("duration", ""),
        "description": description,
    }


def extract_json(text):
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("LLM response did not contain JSON")
    return json.loads(match.group(0))


def rerank_with_llm(query, candidates):
    if not llm_configured() or not candidates:
        return None

    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = (
        os.getenv("LLM_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or DEFAULT_BASE_URL
    ).rstrip("/")
    model = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or DEFAULT_MODEL

    candidate_map = {index: item for index, item in enumerate(candidates)}
    candidate_payload = [
        compact_item(index, item)
        for index, item in candidate_map.items()
    ]

    system_prompt = (
        "You are an SHL assessment recommender. Select only from the provided "
        "catalog candidates. Do not invent assessment names or URLs. Prefer "
        "assessments whose names and descriptions directly match the user's "
        "role, tools, seniority, and requested traits. Return strict JSON only."
    )
    user_prompt = {
        "conversation": query,
        "catalog_candidates": candidate_payload,
        "response_schema": {
            "reply": "short natural language answer",
            "ids": "array of 1 to 10 candidate ids in recommended order"
        },
    }

    response = httpx.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt)},
            ],
        },
        timeout=22,
    )
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    data = extract_json(content)
    ids = data.get("ids", [])

    selected = []
    seen = set()
    for raw_id in ids:
        try:
            candidate_id = int(raw_id)
        except (TypeError, ValueError):
            continue

        item = candidate_map.get(candidate_id)
        if not item or item["url"] in seen:
            continue

        selected.append(item)
        seen.add(item["url"])
        if len(selected) == 10:
            break

    if not selected:
        return None

    return {
        "reply": data.get(
            "reply",
            f"Based on the SHL catalog, here are {len(selected)} matching assessments."
        ),
        "items": selected,
    }

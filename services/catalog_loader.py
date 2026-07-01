import json
from pathlib import Path


CATALOG_PATH = Path("data/shl_catalog.json")


def load_catalog():
    if not CATALOG_PATH.exists():
        raise FileNotFoundError("data/shl_catalog.json not found")

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    clean = []
    for item in data:
        clean.append({
            "name": item.get("name", ""),
            "url": item.get("link", item.get("url", "")),
            "test_type": get_test_type(item.get("keys", [])),
            "description": item.get("description", ""),
            "keys": item.get("keys", []),
            "job_levels": item.get("job_levels", []),
            "duration": item.get("duration", ""),
            "languages": item.get("languages", [])
        })

    return clean


def get_test_type(keys):
    mapping = {
        "Knowledge & Skills": "K",
        "Personality & Behavior": "P",
        "Ability & Aptitude": "A",
        "Biodata & Situational Judgment": "B",
        "Simulations": "S",
        "Competencies": "C",
        "Development & 360": "D",
        "Assessment Exercises": "E"
    }

    types = []
    for key in keys:
        if key in mapping:
            types.append(mapping[key])

    return ",".join(types) if types else "K"
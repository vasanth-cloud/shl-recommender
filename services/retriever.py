import re
from collections import Counter
from difflib import SequenceMatcher

from services.catalog_loader import load_catalog


catalog = load_catalog()

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "have", "i", "in", "is", "it", "need", "of", "on", "or", "our",
    "please", "role", "that", "the", "their", "to", "want", "we", "with",
    "who", "will", "works", "years", "assessment", "assessments", "test",
    "tests", "candidate", "candidates", "hiring", "hire"
}

ALIASES = {
    "backend": ["api", "server", "python", "sql", "programming"],
    "front end": ["frontend", "html", "css", "javascript", "react", "angular"],
    "frontend": ["html", "css", "javascript", "react", "angular"],
    "full stack": ["java", "python", "javascript", "react", "angular", "sql"],
    "stakeholder": ["communication", "situational", "behavior", "personality"],
    "leadership": ["manager", "leadership", "personality", "behavior"],
    "manager": ["management", "leadership", "personality", "behavior"],
    "graduate": ["graduate", "entry-level", "aptitude", "ability"],
    "entry level": ["entry-level", "basic"],
    "mid level": ["mid-professional", "professional"],
    "mid-level": ["mid-professional", "professional"],
    "senior": ["advanced", "professional", "manager"],
    "cognitive": ["ability", "aptitude", "reasoning", "verify"],
    "aptitude": ["ability", "reasoning", "verify"],
    "personality": ["personality", "behavior", "opq"],
    "behaviour": ["personality", "behavior", "opq"],
    "behavior": ["personality", "behavior", "opq"],
    "coding": ["programming", "automata", "java", "python", "javascript"],
    "call center": ["contact center", "customer service", "phone simulation"],
}

ROLE_HINTS = {
    "java developer": ["java", "core java", "java 8", "java frameworks", "sql"],
    "python developer": ["python", "sql", "programming", "automata"],
    "python backend": ["python", "sql", "programming", "automata"],
    "backend developer": ["programming", "sql", "python"],
    "software engineer": ["programming", "software", "agile", "sql"],
    "software engineering": ["programming", "software", "agile", "sql"],
    "software developer": ["programming", "software", "agile", "sql"],
    "frontend developer": ["javascript", "html", "css", "react", "angular"],
    "data analyst": ["python", "sql", "excel", "data science", "numerical"],
    "data scientist": ["python", "sql", "data science", "automata", "numerical"],
    "sales": ["sales", "service", "opq", "communication"],
    "customer service": ["customer service", "contact center", "phone simulation"],
    "manager": ["leadership", "management", "opq", "personality"],
}

PRIORITY_ITEMS = {
    "data analyst": [
        "Python (New)",
        "SQL (New)",
        "Automata - SQL (New)",
        "MS Excel (New)",
        "Microsoft Excel 365 - Essentials (New)",
        "Microsoft Excel 365",
        "Data Science (New)",
        "Automata Data Science (New)",
        "Verify - Numerical Ability",
    ],
    "data scientist": [
        "Data Science (New)",
        "Automata Data Science (New)",
        "Automata Data Science Pro (New)",
        "Python (New)",
        "SQL (New)",
        "Verify - Numerical Ability",
    ],
    "python developer": [
        "Python (New)",
        "Programming Concepts",
        "SQL (New)",
        "Automata - SQL (New)",
    ],
    "python backend": [
        "Python (New)",
        "SQL (New)",
        "Programming Concepts",
        "Automata - SQL (New)",
        "SQL Server (New)",
        "Microsoft SQL Server 2014 Programming",
    ],
    "backend developer": [
        "Programming Concepts",
        "SQL (New)",
        "Python (New)",
        "Automata - SQL (New)",
        "SQL Server (New)",
    ],
    "software engineer": [
        "Programming Concepts",
        "Agile Software Development",
        "SQL (New)",
        "Automata - SQL (New)",
        "Verify - Deductive Reasoning",
        "Verify - Numerical Ability",
    ],
    "software engineering": [
        "Programming Concepts",
        "Agile Software Development",
        "SQL (New)",
        "Automata - SQL (New)",
        "Verify - Deductive Reasoning",
        "Verify - Numerical Ability",
    ],
    "software developer": [
        "Programming Concepts",
        "Agile Software Development",
        "SQL (New)",
        "Automata - SQL (New)",
        "Python (New)",
    ],
    "frontend developer": [
        "HTML/CSS (New)",
        "JavaScript (New)",
        "ReactJS (New)",
        "Automata Front End",
        "CSS3 (New)",
        "HTML5 (New)",
    ],
    "customer service": [
        "Customer Service Phone Simulation",
        "Contact Center Call Simulation (New)",
        "WriteX - Email Writing (Customer Service) (New)",
        "Retail Sales and Service Simulation",
    ],
    "sales": [
        "Occupational Personality Questionnaire OPQ32r",
        "Sales & Service Phone Simulation",
        "Retail Sales and Service Simulation",
        "WriteX - Email Writing (Sales) (New)",
        "Global Skills Assessment",
    ],
}


def tokenize(text: str):
    return [
        token for token in re.findall(r"[a-zA-Z0-9+#.]+", text.lower())
        if token not in STOPWORDS and len(token) > 1
    ]


def expanded_terms(text: str):
    lowered = text.lower()
    terms = Counter(tokenize(lowered))

    for phrase, additions in {**ALIASES, **ROLE_HINTS}.items():
        if phrase in lowered:
            for term in additions:
                terms[term] += 2

    return terms


def item_text(item):
    return " ".join([
        item["name"],
        item["description"],
        " ".join(item["keys"]),
        " ".join(item["job_levels"]),
        " ".join(item["languages"]),
        item.get("duration", "") or "",
    ]).lower()


def is_recommendable(item):
    name = item["name"].lower()
    url = item["url"].lower()
    non_assessment_words = [
        " report", "candidate report", "interview guide", "profiler cards",
        "solution", "development center", "360", " profile"
    ]

    if not item["url"].startswith("https://www.shl.com/products/product-catalog/view/"):
        return False

    if any(word in name or word.replace(" ", "-") in url for word in non_assessment_words):
        return name in {
            "global skills assessment",
            "occupational personality questionnaire opq32r",
        }

    return True


def priority_score(item, lowered_query):
    score = 0.0

    for trigger, names in PRIORITY_ITEMS.items():
        if trigger in lowered_query:
            for index, name in enumerate(names):
                if item["name"] == name:
                    score += 200 - (index * 8)

    explicit_skills = [
        "python", "sql", "excel", "react", "javascript", "html", "css",
        "java", "spring", "aws", "angular", "postgresql", "postgres"
    ]
    for skill in explicit_skills:
        if re.search(rf"\b{re.escape(skill)}\b", lowered_query) and skill in item["name"].lower():
            score += 45

    if re.search(r"\b(postgresql|postgres)\b", lowered_query):
        if item["name"] in {"SQL (New)", "SQL Server (New)", "Automata - SQL (New)", "Programming Concepts"}:
            score += 55
    if "fastapi" in lowered_query and item["name"] in {"Python (New)", "Programming Concepts"}:
        score += 55

    return score


def penalty_score(item, lowered_query):
    name = item["name"].lower()
    penalty = 0.0

    if "data analyst" in lowered_query and name.startswith("data entry") and "data entry" not in lowered_query:
        penalty -= 55
    if "sales" in lowered_query and "salesforce" in name and "salesforce" not in lowered_query:
        penalty -= 60
    if "frontend" in lowered_query and ("asp.net" in name or "informatica" in name):
        penalty -= 35
    if "python" in lowered_query and name.startswith("data entry"):
        penalty -= 35
    if "python" in lowered_query and "java" in name:
        penalty -= 120
    if re.search(r"\b(postgresql|postgres|fastapi)\b", lowered_query) and "java" in name:
        penalty -= 120
    if (
        "software engineer" in lowered_query
        or "software engineering" in lowered_query
        or "software developer" in lowered_query
    ):
        noisy = ["java", "excel", "customer", "sales", "call", "account", "photoshop"]
        if any(word in name for word in noisy) and name != "agile software development":
            penalty -= 60
    if "customer service" in lowered_query or "contact center" in lowered_query:
        allowed = [
            "customer", "contact", "phone", "retail", "writex", "email",
            "sales & service"
        ]
        if not any(word in name for word in allowed):
            penalty -= 80
        if "web services" in name or "aws" in name:
            penalty -= 120
    if re.search(r"\bsales\b", lowered_query) and "salesforce" not in lowered_query:
        allowed = [
            "sales", "retail", "service", "opq", "occupational personality",
            "global skills", "writex"
        ]
        if not any(word in name for word in allowed):
            penalty -= 80
        if name.startswith("sap ") or "telecommunications" in name:
            penalty -= 80

    return penalty


def score_item(item, terms, lowered_query):
    text = item_text(item)
    name = item["name"].lower()
    score = priority_score(item, lowered_query) + penalty_score(item, lowered_query)

    for term, weight in terms.items():
        if term in name:
            score += 7 * weight
        if term in text:
            score += 2 * weight

    if "advanced" in name and any(t in terms for t in ["senior", "experienced", "advanced"]):
        score += 6
    if "entry" in name and any(t in terms for t in ["entry", "graduate", "junior"]):
        score += 5
    if "new" in name:
        score += 0.5

    requested_types = []
    if any(t in terms for t in ["personality", "behavior", "behaviour", "opq"]):
        requested_types.append("P")
    if any(t in terms for t in ["cognitive", "aptitude", "ability", "reasoning", "numerical"]):
        requested_types.append("A")
    if any(t in terms for t in ["simulation", "coding"]):
        requested_types.append("S")

    if requested_types and any(t in item["test_type"].split(",") for t in requested_types):
        score += 8

    return score


def search_catalog(query: str, top_k: int = 10, recommendable_only: bool = True):
    terms = expanded_terms(query)
    lowered_query = query.lower()
    ranked = []

    for item in catalog:
        if recommendable_only and not is_recommendable(item):
            continue
        score = score_item(item, terms, lowered_query)
        if score > 0:
            ranked.append((item, score))

    ranked.sort(key=lambda pair: pair[1], reverse=True)
    return [item for item, _ in ranked[:top_k]]


def find_catalog_items(text: str, limit: int = 5):
    lowered = text.lower()
    matches = []
    exact_aliases = {
        "opq": "Occupational Personality Questionnaire OPQ32r",
        "opq32": "Occupational Personality Questionnaire OPQ32r",
        "opq32r": "Occupational Personality Questionnaire OPQ32r",
        "gsa": "Global Skills Assessment",
        "global skills assessment": "Global Skills Assessment",
        "verify g+": "Verify - G+",
    }

    for alias, target_name in exact_aliases.items():
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            for item in catalog:
                if item["name"] == target_name:
                    matches.append((item, 1.0))

    for item in catalog:
        name = item["name"].lower()
        compact_name = re.sub(r"[^a-z0-9]+", " ", name).strip()
        if name in lowered or compact_name in lowered:
            matches.append((item, 1.0))
            continue

        abbreviations = re.findall(r"\b[A-Z][A-Z0-9+]{1,}\b", item["name"])
        if any(len(abbr) >= 3 and re.search(rf"\b{re.escape(abbr.lower())}\b", lowered) for abbr in abbreviations):
            matches.append((item, 0.95))
            continue

        ratio = SequenceMatcher(None, compact_name, lowered).ratio()
        if ratio >= 0.55:
            matches.append((item, ratio))

    matches.sort(key=lambda pair: pair[1], reverse=True)
    if matches:
        unique = []
        seen = set()
        for item, _ in matches:
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            unique.append(item)
            if len(unique) == limit:
                break
        return unique

    return search_catalog(text, top_k=limit, recommendable_only=False)

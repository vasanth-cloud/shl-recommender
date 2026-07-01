import re
from rank_bm25 import BM25Okapi
from services.catalog_loader import load_catalog


catalog = load_catalog()


def tokenize(text: str):
    return re.findall(r"[a-zA-Z0-9+#.]+", text.lower())


documents = [
    " ".join([
        item["name"] * 3,
        item["description"],
        " ".join(item["keys"])
    ])
    for item in catalog
]

tokenized_docs = [tokenize(doc) for doc in documents]
bm25 = BM25Okapi(tokenized_docs)


def search_catalog(query: str, top_k: int = 10):
    tokens = tokenize(query)
    scores = bm25.get_scores(tokens)

    ranked = sorted(
        zip(catalog, scores),
        key=lambda x: x[1],
        reverse=True
    )

    results = []
    seen = set()

    for item, score in ranked:
        if item["name"] in seen:
            continue

        if score <= 0:
            continue

        seen.add(item["name"])
        results.append(item)

        if len(results) >= top_k:
            break

    return results
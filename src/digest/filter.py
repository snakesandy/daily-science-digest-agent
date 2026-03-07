from __future__ import annotations

from digest.models import Article

EXCLUDED_KEYWORDS = {
    "podcast", "video", "multimedia", "episode", "listen", "watch",
    "webinar", "livestream", "retraction", "erratum", "correction",
}

# Tightly focused: algorithms, math, AI/ML
TOPIC_KEYWORDS = {
    # Mathematics
    "mathematics", "math", "algebra", "geometry", "topology", "number theory",
    "proof", "conjecture", "theorem", "combinatorics", "optimization",
    "cryptography", "graph theory", "category theory", "probability",
    # Algorithms & CS
    "algorithm", "computation", "complexity", "np-hard", "polynomial time",
    "data structure", "approximation", "heuristic", "solver",
    # AI & Machine Learning
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "large language model", "llm", "transformer",
    "reinforcement learning", "generative model", "diffusion model",
    "computer vision", "natural language processing", "reasoning",
    # Quantum computing (algorithmic side)
    "quantum computing", "quantum algorithm", "qubit",
}

# Innovation signals
INNOVATION_KEYWORDS = {
    "breakthrough", "discovery", "novel", "new method", "new approach",
    "first", "invented", "invention", "advance", "innovation",
    "unprecedented", "state-of-the-art", "outperforms", "surpasses",
    "solved", "proves", "disproves", "faster", "efficient",
}

# Off-topic penalties — articles heavy in these get scored down
OFFTOPIC_KEYWORDS = {
    "biology", "biomedical", "clinical", "patient", "disease", "cancer",
    "drug", "therapy", "treatment", "cell", "protein", "gene", "dna",
    "ecology", "species", "biodiversity", "marine", "wildlife", "animal",
    "climate change", "weather", "ocean", "fossil", "geological",
    "psychology", "mental health", "brain scan", "cognitive", "neuroscience",
    "nutrition", "diet", "exercise", "sleep",
    "policy", "politics", "regulation", "funding", "editorial", "scandal",
    "chemistry", "chemical", "molecule", "organic", "inorganic",
    "transplant", "surgery", "liver", "kidney", "heart attack",
    "fish", "plant", "flower", "insect", "bacteria", "virus",
}


def filter_articles(articles: list[Article]) -> list[Article]:
    return [a for a in articles if _is_valid_article(a) and score_relevance(a) > 0]


def score_relevance(article: Article) -> float:
    text = f"{article.title} {article.description} {' '.join(article.categories)}".lower()
    category_hits = sum(1 for kw in TOPIC_KEYWORDS if kw in {c.lower() for c in article.categories})
    text_hits = sum(1 for kw in TOPIC_KEYWORDS if kw in text)
    innovation_hits = sum(1 for kw in INNOVATION_KEYWORDS if kw in text)
    offtopic_hits = sum(1 for kw in OFFTOPIC_KEYWORDS if kw in text)

    score = category_hits * 2.0 + text_hits * 0.5 + innovation_hits * 1.5
    score -= offtopic_hits * 2.0
    return max(min(score, 10.0), 0.0)


def _is_valid_article(article: Article) -> bool:
    if article.content_type != "article":
        return False
    text = f"{article.title} {article.url}".lower()
    return not any(kw in text for kw in EXCLUDED_KEYWORDS)

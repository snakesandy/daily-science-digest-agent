from __future__ import annotations

import re

from digest.models import Article

EXCLUDED_KEYWORDS = {
    "podcast", "video", "multimedia", "episode", "listen", "watch",
    "webinar", "livestream", "retraction", "erratum", "correction",
}

# AI/ML keywords get extra weight (scored separately)
AIML_KEYWORDS = {
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "large language model", "llm", "transformer model",
    "reinforcement learning", "generative model", "diffusion model",
    "computer vision", "natural language processing",
    "gpt", "chatbot", "ai agent", "fine-tuning", "pretraining",
    "multimodal model", "foundation model", "rlhf",
    "text-to-image", "text-to-video", "image generation",
    "embeddings", "vector database",
    "robotics", "self-driving",
    "openai", "google deepmind", "anthropic", "meta ai",
    "image recognition", "speech recognition", "object detection",
    "language model", "training data", "neural architecture",
    "convolutional neural", "recurrent neural", "attention mechanism",
    "backpropagation", "classification model",
    "generative ai", "ai model", "ai system", "ai safety",
}

# Other on-topic keywords
TOPIC_KEYWORDS = {
    # Mathematics (specific, not generic "math")
    "mathematics", "algebra", "topology", "number theory",
    "conjecture", "combinatorics",
    "cryptography", "graph theory", "category theory",
    # Algorithms & CS
    "algorithm design", "computational complexity", "np-hard", "polynomial time",
    "data structure", "heuristic",
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

# Off-topic penalties
OFFTOPIC_KEYWORDS = {
    # Biology / medicine
    "biology", "biomedical", "clinical", "patient", "disease", "cancer",
    "drug", "therapy", "treatment", "cell", "protein", "gene", "dna",
    "genome", "genomic", "pangenome", "phenotype", "genotype", "sequencing",
    "rna", "mrna", "crispr", "biomarker", "pathogen", "epidemiology",
    "transplant", "surgery", "liver", "kidney", "heart attack",
    "fish", "plant", "flower", "insect", "bacteria", "virus",
    "sorghum", "crop", "seed", "wheat", "maize", "rice",
    # Ecology / earth science
    "ecology", "species", "biodiversity", "marine", "wildlife", "animal",
    "climate change", "weather", "ocean", "fossil", "geological",
    "seismic", "tectonic", "volcanic", "mineral", "soil",
    # Psychology / neuro
    "psychology", "mental health", "brain scan", "cognitive", "neuroscience",
    "nutrition", "diet", "exercise", "sleep",
    # Policy / social
    "policy", "politics", "regulation", "funding", "editorial", "scandal",
    # Chemistry / materials
    "chemistry", "chemical", "molecule", "organic", "inorganic",
    "catalyst", "polymer", "alloy", "ceramic", "corrosion",
    # Traditional physics / engineering (not CS/AI relevant)
    "electromagnetic", "scattering", "antenna", "porous media",
    "fluid dynamics", "turbulence", "navier-stokes", "aerodynamic",
    "thermodynamic", "plasma", "photonic", "photovoltaic",
    "semiconductor", "superconductor", "magnetism", "ferromagnetic",
    "nuclear", "fission", "fusion", "reactor", "isotope",
    "spectroscopy", "crystallography", "diffraction",
    "astrophysics", "cosmology", "stellar", "galactic", "exoplanet",
    "gravitational wave", "dark matter", "dark energy", "black hole",
    "seismology", "geophysics", "oceanography", "meteorology",
    "hydraulic", "structural engineering", "civil engineering",
    "mechanical engineering", "aerospace",
    # Wireless / telecom / signal processing
    "wireless", "antenna", "beamforming", "mimo", "ofdm",
    "cellular network", "5g", "6g", "spectrum", "modulation",
    "channel estimation", "signal processing", "radar",
    "satellite", "terrestrial network",
    # Applied domains that use ML but aren't about ML
    "cardiac", "defibrillator", "medical device",
    "power grid", "smart grid", "energy storage",
    "traffic flow", "vehicle routing",
    "inventory", "supply chain", "logistics",
    "network slicing", "ran slicing",
}


def _count_keyword_hits(keywords: set[str], text: str) -> int:
    """Count keyword hits using word-boundary matching to avoid substring false positives."""
    return sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text))


def filter_articles(articles: list[Article]) -> list[Article]:
    return [a for a in articles if _is_valid_article(a) and _passes_relevance(a)]


def _passes_relevance(article: Article) -> bool:
    score = score_relevance(article)
    if score < 1.0:
        return False
    # Check title + description only (not categories, to avoid cs.AI false positives)
    content_text = f"{article.title} {article.description}".lower()
    has_aiml = any(re.search(r'\b' + re.escape(kw) + r'\b', content_text) for kw in AIML_KEYWORDS)
    has_topic = any(re.search(r'\b' + re.escape(kw) + r'\b', content_text) for kw in TOPIC_KEYWORDS)
    # All sources must have at least one on-topic keyword
    if not has_aiml and not has_topic:
        return False
    # arXiv needs higher bar + must have AI/ML keyword
    if article.source == "arxiv":
        return score >= 2.0 and has_aiml
    return True


def score_relevance(article: Article) -> float:
    text = f"{article.title} {article.description} {' '.join(article.categories)}".lower()
    lower_cats = {c.lower() for c in article.categories}

    # AI/ML gets double weight
    aiml_cat_hits = sum(1 for kw in AIML_KEYWORDS if kw in lower_cats)
    aiml_text_hits = _count_keyword_hits(AIML_KEYWORDS, text)
    aiml_score = aiml_cat_hits * 3.0 + aiml_text_hits * 1.0

    # Other topics
    topic_cat_hits = sum(1 for kw in TOPIC_KEYWORDS if kw in lower_cats)
    topic_text_hits = _count_keyword_hits(TOPIC_KEYWORDS, text)
    topic_score = topic_cat_hits * 2.0 + topic_text_hits * 0.5

    innovation_hits = _count_keyword_hits(INNOVATION_KEYWORDS, text)
    offtopic_hits = _count_keyword_hits(OFFTOPIC_KEYWORDS, text)

    score = aiml_score + topic_score + innovation_hits * 1.5
    score -= offtopic_hits * 2.0
    return max(min(score, 10.0), 0.0)


def _is_valid_article(article: Article) -> bool:
    if article.content_type != "article":
        return False
    text = f"{article.title} {article.url}".lower()
    return not any(kw in text for kw in EXCLUDED_KEYWORDS)

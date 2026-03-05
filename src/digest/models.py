from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    title: str
    url: str
    source: str  # "quanta" | "scientific_american"
    published: datetime
    categories: list[str] = field(default_factory=list)
    description: str = ""
    content_type: str = "article"  # "article" | "podcast" | "video"
    summary: str | None = None
    relevance_score: float = 0.0

from __future__ import annotations

from datetime import datetime, timezone

import feedparser

from digest.models import Article
from digest.sources.base import ArticleSource

FEED_URL = "https://www.quantamagazine.org/feed/"

NON_ARTICLE_CATEGORIES = {"podcast", "multimedia", "video", "podcasts", "videos"}


class QuantaSource(ArticleSource):
    def fetch(self, since: datetime) -> list[Article]:
        feed = feedparser.parse(FEED_URL)
        articles = []
        for entry in feed.entries:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if published < since:
                continue

            categories = [tag.term for tag in getattr(entry, "tags", [])]
            content_type = _detect_content_type(categories, entry.get("link", ""))

            articles.append(
                Article(
                    title=entry.title,
                    url=entry.link,
                    source="quanta",
                    published=published,
                    categories=categories,
                    description=getattr(entry, "summary", ""),
                    content_type=content_type,
                )
            )
        return articles


def _detect_content_type(categories: list[str], url: str) -> str:
    lower_cats = {c.lower() for c in categories}
    if lower_cats & NON_ARTICLE_CATEGORIES:
        return "podcast" if "podcast" in lower_cats or "podcasts" in lower_cats else "video"
    if "/podcast/" in url or "/video/" in url:
        return "podcast" if "/podcast/" in url else "video"
    return "article"

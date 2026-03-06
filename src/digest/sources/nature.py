from __future__ import annotations

from datetime import datetime, timezone

import feedparser

from digest.models import Article
from digest.sources.base import ArticleSource

FEED_URL = "https://www.nature.com/nature.rss"

NON_ARTICLE_TYPES = {"podcast", "video", "correction", "erratum", "retraction"}


class NatureSource(ArticleSource):
    def fetch(self, since: datetime) -> list[Article]:
        feed = feedparser.parse(FEED_URL)
        articles = []
        for entry in feed.entries:
            pub_parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
            if not pub_parsed:
                continue
            published = datetime(*pub_parsed[:6], tzinfo=timezone.utc)
            if published < since:
                continue

            categories = [tag.term for tag in getattr(entry, "tags", [])]
            content_type = _detect_content_type(categories, entry.get("link", ""))

            articles.append(
                Article(
                    title=entry.title,
                    url=entry.link,
                    source="nature",
                    published=published,
                    categories=categories,
                    description=getattr(entry, "summary", ""),
                    content_type=content_type,
                )
            )
        return articles


def _detect_content_type(categories: list[str], url: str) -> str:
    lower_cats = {c.lower() for c in categories}
    if lower_cats & NON_ARTICLE_TYPES:
        return "other"
    if "/podcast/" in url or "/video/" in url:
        return "podcast" if "/podcast/" in url else "video"
    return "article"

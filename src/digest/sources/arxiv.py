from __future__ import annotations

from datetime import datetime, timezone

import feedparser

from digest.models import Article
from digest.sources.base import ArticleSource

# arXiv RSS feeds for target topics
FEED_URLS = [
    ("https://rss.arxiv.org/rss/math", "Mathematics"),
    ("https://rss.arxiv.org/rss/cs.AI", "Artificial Intelligence"),
    ("https://rss.arxiv.org/rss/cs.LG", "Machine Learning"),
    ("https://rss.arxiv.org/rss/physics", "Physics"),
]


class ArxivSource(ArticleSource):
    def fetch(self, since: datetime) -> list[Article]:
        articles = []
        seen_urls = set()
        for feed_url, default_category in FEED_URLS:
            try:
                articles.extend(_parse_feed(feed_url, default_category, since, seen_urls))
            except Exception as e:
                print(f"Warning: Failed to fetch arXiv feed {feed_url}: {e}")
        return articles


def _parse_feed(
    feed_url: str, default_category: str, since: datetime, seen_urls: set[str]
) -> list[Article]:
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries:
        pub_parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if pub_parsed:
            published = datetime(*pub_parsed[:6], tzinfo=timezone.utc)
        else:
            # arXiv RSS sometimes lacks dates; use since as approximate
            published = since

        if pub_parsed and published < since:
            continue

        url = entry.link
        # Normalize arXiv URLs (abs vs pdf)
        url = url.replace("/pdf/", "/abs/").rstrip(".pdf")
        if url in seen_urls:
            continue
        seen_urls.add(url)

        categories = [tag.term for tag in getattr(entry, "tags", [])]
        if not categories:
            categories = [default_category]

        articles.append(
            Article(
                title=_clean_title(entry.title),
                url=url,
                source="arxiv",
                published=published,
                categories=categories,
                description=_clean_description(getattr(entry, "summary", "")),
                content_type="article",
            )
        )
    return articles


def _clean_title(title: str) -> str:
    # arXiv titles sometimes have "Title (arXiv:XXXX.XXXXX ...)" suffix
    if "(arXiv:" in title:
        title = title[: title.index("(arXiv:")].strip()
    return title


def _clean_description(desc: str) -> str:
    # Strip HTML tags from arXiv summaries
    import re
    return re.sub(r"<[^>]+>", "", desc).strip()

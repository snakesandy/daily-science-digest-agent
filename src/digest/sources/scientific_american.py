from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from digest.models import Article
from digest.sources.base import ArticleSource

LATEST_URL = "https://www.scientificamerican.com/latest/"

EXCLUDED_URL_PATTERNS = ["/podcast/", "/video/", "/custom-media/", "/podcast-episode/"]


class ScientificAmericanSource(ArticleSource):
    def fetch(self, since: datetime) -> list[Article]:
        resp = httpx.get(LATEST_URL, headers={"User-Agent": "DailyScienceDigest/0.1"}, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        articles = _parse_json_ld(resp.text, since)
        if not articles:
            articles = _parse_html(resp.text, since)
        return articles


def _parse_json_ld(html: str, since: datetime) -> list[Article]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if item.get("@type") not in ("Article", "NewsArticle", "ScholarlyArticle", "BlogPosting"):
                continue
            url = item.get("url", "")
            if any(p in url for p in EXCLUDED_URL_PATTERNS):
                continue
            pub_str = item.get("datePublished", "")
            published = _parse_date(pub_str)
            if not published or published < since:
                continue
            articles.append(
                Article(
                    title=item.get("headline", ""),
                    url=url,
                    source="scientific_american",
                    published=published,
                    description=item.get("description", ""),
                    content_type="article",
                )
            )
    return articles


def _parse_html(html: str, since: datetime) -> list[Article]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    for link_tag in soup.select("a[href*='/article/']"):
        url = link_tag.get("href", "")
        if not url.startswith("http"):
            url = "https://www.scientificamerican.com" + url
        if any(p in url for p in EXCLUDED_URL_PATTERNS):
            continue

        # Extract clean title from h2, fallback to full link text
        h2 = link_tag.select_one("h2")
        title = h2.get_text(strip=True) if h2 else link_tag.get_text(strip=True)
        if not title or len(title) < 10:
            continue

        # Extract category from kicker container
        categories = []
        kicker = link_tag.select_one("div[class*='kicker']")
        if kicker:
            kicker_text = kicker.get_text(strip=True)
            # Remove date portion (e.g. "March 5, 2026")
            cat = re.sub(r"[A-Z][a-z]+ \d{1,2}, \d{4}$", "", kicker_text).strip()
            if cat:
                categories = [cat]

        # Avoid duplicates within the same parse
        if any(a.url == url for a in articles):
            continue
        articles.append(
            Article(
                title=title,
                url=url,
                source="scientific_american",
                published=since,  # approximate; no date available from card
                description="",
                categories=categories,
                content_type="article",
            )
        )
    return articles


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    # Try ISO format
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str[:26].rstrip("Z"), fmt.replace("%z", ""))
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    # Strip timezone suffix and try again
    clean = re.sub(r"[+-]\d{2}:\d{2}$", "", date_str)
    try:
        return datetime.strptime(clean, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None

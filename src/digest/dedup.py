from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from digest.models import Article


class DedupStore:
    def __init__(self, data_dir: str = "./data"):
        self.path = Path(data_dir) / "seen_articles.json"
        self.seen: dict[str, str] = {}  # url -> date string
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self.seen = json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError):
                self.seen = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.seen, indent=2))

    def filter_new(self, articles: list[Article]) -> list[Article]:
        return [a for a in articles if a.url not in self.seen]

    def mark_seen(self, articles: list[Article]) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for a in articles:
            self.seen[a.url] = today

    def prune(self, max_age_days: int = 30) -> None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).strftime("%Y-%m-%d")
        self.seen = {url: date for url, date in self.seen.items() if date >= cutoff}

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from digest.models import Article


class ArticleSource(ABC):
    @abstractmethod
    def fetch(self, since: datetime) -> list[Article]:
        """Fetch articles published since the given datetime."""

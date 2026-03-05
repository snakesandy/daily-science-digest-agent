import json
from datetime import datetime, timezone

from digest.dedup import DedupStore
from digest.models import Article


def _make_article(url="https://example.com/test"):
    return Article(
        title="Test",
        url=url,
        source="quanta",
        published=datetime(2026, 3, 5, tzinfo=timezone.utc),
    )


def test_filter_new_empty_store(tmp_path):
    store = DedupStore(str(tmp_path))
    articles = [_make_article("https://example.com/1")]
    assert len(store.filter_new(articles)) == 1


def test_filter_new_skips_seen(tmp_path):
    store = DedupStore(str(tmp_path))
    store.seen["https://example.com/1"] = "2026-03-05"
    articles = [_make_article("https://example.com/1")]
    assert len(store.filter_new(articles)) == 0


def test_mark_seen_and_persist(tmp_path):
    store = DedupStore(str(tmp_path))
    articles = [_make_article("https://example.com/1")]
    store.mark_seen(articles)
    store.save()

    store2 = DedupStore(str(tmp_path))
    assert "https://example.com/1" in store2.seen


def test_prune_old_entries(tmp_path):
    store = DedupStore(str(tmp_path))
    store.seen = {
        "https://example.com/old": "2026-01-01",
        "https://example.com/new": "2026-03-05",
    }
    store.prune(max_age_days=30)
    assert "https://example.com/old" not in store.seen
    assert "https://example.com/new" in store.seen


def test_handles_corrupt_file(tmp_path):
    path = tmp_path / "seen_articles.json"
    path.write_text("not json")
    store = DedupStore(str(tmp_path))
    assert store.seen == {}

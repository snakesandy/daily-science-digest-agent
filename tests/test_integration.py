from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import feedparser

from digest.main import run

FIXTURES = Path(__file__).parent / "fixtures"


def test_full_pipeline_dry_run(tmp_path, monkeypatch):
    """End-to-end test: fetch from mocked sources, filter, rank, output (no API call)."""
    feed_xml = (FIXTURES / "quanta_feed.xml").read_text()
    sciam_html = (FIXTURES / "sciam_page.html").read_text()

    class FakeResponse:
        status_code = 200
        def __init__(self, text):
            self.text = text
        def raise_for_status(self):
            pass

    monkeypatch.setenv("DIGEST_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "")

    with (
        patch("digest.sources.quanta.feedparser") as mock_fp,
        patch("digest.sources.scientific_american.httpx.get") as mock_get,
        patch("digest.main.datetime") as mock_dt,
    ):
        mock_fp.parse.return_value = feedparser.parse(feed_xml)
        mock_get.return_value = FakeResponse(sciam_html)
        mock_dt.now.return_value = datetime(2026, 3, 5, 14, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        articles = run(dry_run=True)

    # Should have articles, no podcasts/videos
    assert len(articles) > 0
    assert all(a.content_type == "article" for a in articles)
    # No podcast URLs
    assert not any("/podcast/" in a.url for a in articles)
    # Dedup file created
    assert (tmp_path / "seen_articles.json").exists()


def test_full_pipeline_with_summarization(tmp_path, monkeypatch):
    """End-to-end test with mocked OpenAI API."""
    feed_xml = (FIXTURES / "quanta_feed.xml").read_text()
    sciam_html = (FIXTURES / "sciam_page.html").read_text()

    class FakeResponse:
        status_code = 200
        def __init__(self, text):
            self.text = text
        def raise_for_status(self):
            pass

    monkeypatch.setenv("DIGEST_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    mock_message = MagicMock()
    mock_message.content = (
        "1. Researchers developed a quantum algorithm that solves optimization problems exponentially faster.\n"
        "2. A deep learning model predicts protein structures with record accuracy, advancing drug discovery.\n"
        "3. Observations of a black hole challenge general relativity predictions.\n"
        "4. A new neural network mirrors human brain connectivity patterns.\n"
        "5. Mathematicians proved a prime distribution conjecture with cryptography implications.\n"
        "6. Climate study reveals marine biodiversity decline.\n"
    )
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with (
        patch("digest.sources.quanta.feedparser") as mock_fp,
        patch("digest.sources.scientific_american.httpx.get") as mock_get,
        patch("digest.main.datetime") as mock_dt,
        patch("digest.summarizer.OpenAI") as mock_openai,
    ):
        mock_fp.parse.return_value = feedparser.parse(feed_xml)
        mock_get.return_value = FakeResponse(sciam_html)
        mock_dt.now.return_value = datetime(2026, 3, 5, 14, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        articles = run(dry_run=False)

    assert len(articles) > 0
    summaries = [a.summary for a in articles if a.summary]
    assert len(summaries) > 0

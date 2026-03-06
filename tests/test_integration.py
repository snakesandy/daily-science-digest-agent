from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import feedparser

from digest.main import run

FIXTURES = Path(__file__).parent / "fixtures"


def test_full_pipeline_dry_run(tmp_path, monkeypatch):
    """End-to-end test: fetch from mocked sources, filter, rank, output (no API call)."""
    quanta_xml = (FIXTURES / "quanta_feed.xml").read_text()
    nature_xml = (FIXTURES / "nature_feed.xml").read_text()
    arxiv_xml = (FIXTURES / "arxiv_feed.xml").read_text()

    monkeypatch.setenv("DIGEST_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "")

    with (
        patch("digest.sources.quanta.feedparser") as mock_quanta_fp,
        patch("digest.sources.nature.feedparser") as mock_nature_fp,
        patch("digest.sources.arxiv.feedparser") as mock_arxiv_fp,
        patch("digest.main.datetime") as mock_dt,
    ):
        mock_quanta_fp.parse.return_value = feedparser.parse(quanta_xml)
        mock_nature_fp.parse.return_value = feedparser.parse(nature_xml)
        mock_arxiv_fp.parse.return_value = feedparser.parse(arxiv_xml)
        mock_dt.now.return_value = datetime(2026, 3, 5, 14, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        articles = run(dry_run=True)

    # Should have articles, no podcasts/videos
    assert len(articles) > 0
    assert all(a.content_type == "article" for a in articles)
    # No podcast URLs
    assert not any("/podcast/" in a.url for a in articles)
    # Multiple sources represented
    sources = {a.source for a in articles}
    assert len(sources) >= 2
    # Dedup file created
    assert (tmp_path / "seen_articles.json").exists()


def test_full_pipeline_with_summarization(tmp_path, monkeypatch):
    """End-to-end test with mocked OpenAI API."""
    quanta_xml = (FIXTURES / "quanta_feed.xml").read_text()
    nature_xml = (FIXTURES / "nature_feed.xml").read_text()
    arxiv_xml = (FIXTURES / "arxiv_feed.xml").read_text()

    monkeypatch.setenv("DIGEST_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    mock_message = MagicMock()
    mock_message.content = (
        "1. A quantum error correction code achieves record fidelity, advancing quantum computing.\n"
        "2. A graph neural network solves NP-hard optimization problems faster than existing methods.\n"
        "3. A new proof simplifies the Riemann hypothesis for function fields.\n"
        "4. A quantum algorithm solves optimization problems exponentially faster.\n"
        "5. A deep learning model predicts protein structures with record accuracy.\n"
        "6. CRISPR achieves unprecedented precision in plant genome editing.\n"
    )
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with (
        patch("digest.sources.quanta.feedparser") as mock_quanta_fp,
        patch("digest.sources.nature.feedparser") as mock_nature_fp,
        patch("digest.sources.arxiv.feedparser") as mock_arxiv_fp,
        patch("digest.main.datetime") as mock_dt,
        patch("digest.summarizer.OpenAI") as mock_openai,
    ):
        mock_quanta_fp.parse.return_value = feedparser.parse(quanta_xml)
        mock_nature_fp.parse.return_value = feedparser.parse(nature_xml)
        mock_arxiv_fp.parse.return_value = feedparser.parse(arxiv_xml)
        mock_dt.now.return_value = datetime(2026, 3, 5, 14, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        articles = run(dry_run=False)

    assert len(articles) > 0
    summaries = [a.summary for a in articles if a.summary]
    assert len(summaries) > 0

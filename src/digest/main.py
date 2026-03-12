from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from digest.dedup import DedupStore
from digest.filter import filter_articles
from digest.models import Article
from digest.output import ConsoleOutput, TelegramOutput
from digest.ranker import rank_and_select
from digest.sources import ArxivSource, NatureSource, QuantaSource
from digest.summarizer import summarize_articles


def run(dry_run: bool = False) -> list[Article]:
    load_dotenv()

    api_key = os.environ.get("OPENAI_API_KEY", "")
    data_dir = os.environ.get("DIGEST_DATA_DIR", "./data")
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not dry_run and not api_key:
        print("Error: OPENAI_API_KEY not set. Use --dry-run or set in .env", file=sys.stderr)
        sys.exit(1)

    since = datetime.now(timezone.utc) - timedelta(days=7)

    # 1. Fetch from all sources
    sources = [QuantaSource(), NatureSource(), ArxivSource()]
    all_articles: list[Article] = []
    for source in sources:
        try:
            articles = source.fetch(since)
            print(f"Fetched {len(articles)} articles from {source.__class__.__name__}")
            all_articles.extend(articles)
        except Exception as e:
            print(f"Warning: Failed to fetch from {source.__class__.__name__}: {e}")

    # 2. Deduplicate
    dedup = DedupStore(data_dir)
    dedup.prune()
    all_articles = dedup.filter_new(all_articles)
    print(f"{len(all_articles)} new articles after dedup")

    # 3. Filter podcasts/videos and score relevance
    all_articles = filter_articles(all_articles)
    print(f"{len(all_articles)} articles after filtering")

    # 4. Rank and select top 10
    top_articles = rank_and_select(all_articles, top_n=10)

    # 5. Summarize
    if not dry_run:
        top_articles = summarize_articles(top_articles, api_key)
    else:
        print("[Dry run] Skipping summarization")

    # 6. Output
    now = datetime.now(timezone.utc)
    outputs = [ConsoleOutput()]
    if telegram_token and telegram_chat_id:
        chat_ids = [cid.strip() for cid in telegram_chat_id.split(",") if cid.strip()]
        outputs.append(TelegramOutput(telegram_token, chat_ids))
    for output in outputs:
        output.send(top_articles, now)

    # 7. Mark as seen and save
    dedup.mark_seen(top_articles)
    dedup.save()

    return top_articles


def main():
    parser = argparse.ArgumentParser(description="Daily Science Digest")
    parser.add_argument("--dry-run", action="store_true", help="Skip summarization (no API key needed)")
    args = parser.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()

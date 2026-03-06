# Daily Science Digest Agent

A daily morning digest agent that selects the 10 best new articles from Scientific American and Quanta Magazine, summarizes them using OpenAI GPT-4o-mini, and delivers clickable links with summaries to Telegram every morning at 6:00 AM EST.

## How It Works

```
RSS/HTML Fetch → Deduplicate → Filter → Rank → Summarize → Deliver
```

1. **Fetch** articles from Quanta Magazine (RSS feed) and Scientific American (HTML scraping)
2. **Deduplicate** against previously seen articles (JSON file store, 30-day retention)
3. **Filter** out podcasts, videos, and multimedia content
4. **Rank** by topic relevance (AI, math, physics) + recency + priority keywords (discovery, breakthrough, etc.)
5. **Summarize** the top 10 via OpenAI GPT-4o-mini (1-2 sentences: what's new + why it matters)
6. **Deliver** to console and Telegram

## Project Structure

```
daily-science-digest-agent/
├── .github/workflows/
│   └── digest.yml               # GitHub Actions cron (6am EST daily)
├── src/digest/
│   ├── main.py                  # CLI entry point + orchestrator
│   ├── models.py                # Article dataclass
│   ├── sources/
│   │   ├── base.py              # ArticleSource ABC
│   │   ├── quanta.py            # RSS via feedparser
│   │   └── scientific_american.py  # HTML scraping + JSON-LD fallback
│   ├── filter.py                # Podcast/video exclusion + topic scoring
│   ├── ranker.py                # Score + select top 10
│   ├── summarizer.py            # OpenAI GPT-4o-mini summarization
│   ├── dedup.py                 # JSON-file dedup store
│   └── output.py                # ConsoleOutput + TelegramOutput
├── tests/                       # 24 tests, all mocked (no API keys needed)
│   ├── test_filter.py
│   ├── test_dedup.py
│   ├── test_ranker.py
│   ├── test_sources.py
│   ├── test_integration.py
│   └── fixtures/
│       ├── quanta_feed.xml
│       └── sciam_page.html
├── data/                        # Runtime (gitignored)
│   └── seen_articles.json
├── pyproject.toml
├── .env.example
├── .gitignore
└── run_digest.sh                # Local runner script
```

## Setup

### Prerequisites

- Python 3.11+
- An OpenAI API key
- A Telegram bot token and chat ID (for Telegram delivery)

### Installation

```bash
git clone https://github.com/snakesandy/daily-science-digest-agent.git
cd daily-science-digest-agent
pip install -e ".[dev]"
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```
OPENAI_API_KEY=sk-proj-...       # Required
TELEGRAM_BOT_TOKEN=123456:ABC... # Optional (for Telegram delivery)
TELEGRAM_CHAT_ID=123456789       # Optional (for Telegram delivery)
DIGEST_DATA_DIR=./data           # Optional (defaults to ./data)
```

### Setting Up Telegram

1. Open Telegram and message **@BotFather**
2. Send `/newbot`, choose a name and username
3. Copy the bot token BotFather gives you
4. Open your new bot in Telegram and send it any message (e.g. "hello")
5. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser
6. Find your chat ID in the response: `"chat":{"id":123456789}`
7. Add both values to your `.env` file

## Usage

### Run the digest (with summaries + Telegram)

```bash
python -m digest
```

### Dry run (no API calls, no Telegram)

```bash
python -m digest --dry-run
```

### Run tests

```bash
pytest tests/ -v
```

## Scheduling

### GitHub Actions (recommended)

The repo includes a GitHub Actions workflow (`.github/workflows/digest.yml`) that runs automatically every day at 6:00 AM EST (11:00 UTC).

To use it, add these secrets in your GitHub repo settings (Settings > Secrets and variables > Actions):

- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

You can also trigger a run manually from the Actions tab using the "Run workflow" button.

### Local cron (alternative)

If you prefer running locally:

```bash
# Make the runner script executable
chmod +x run_digest.sh

# Add to crontab (6am EST = 11:00 UTC)
crontab -e
# Add this line:
0 11 * * * /path/to/daily-science-digest-agent/run_digest.sh
```

Note: local cron requires your machine to be awake at the scheduled time.

## Configuration

### Topic Priorities

The agent prioritizes articles about:
- **AI**: artificial intelligence, machine learning, deep learning, neural networks, LLMs
- **Mathematics**: algebra, geometry, topology, number theory, proofs
- **Physics**: quantum, particle physics, cosmology, astrophysics, black holes

These keywords are defined in `src/digest/filter.py` and can be modified.

### Ranking

Articles are scored by:
- **Topic relevance** (0-10): keyword matches in title, description, and categories
- **Recency bonus** (0-3): newer articles score higher
- **Priority keywords** (0-5): "discovery", "breakthrough", "new", "first", "novel", etc.

### Fetch Window

Articles from the last 3 days are fetched to ensure Quanta Magazine (which publishes less frequently) is well represented. Already-seen articles are excluded via deduplication.

## Output Example

```
=== Daily Science Digest — March 5, 2026 ===

1) New Quantum Algorithm Breaks Speed Record
   Researchers discovered a quantum algorithm that solves optimization problems
   exponentially faster than classical methods. This could transform cryptography
   and drug discovery.
   https://www.quantamagazine.org/new-quantum-algorithm-20260305/

2) IBM Scientists Unveil First "Half-Möbius" Molecule
   IBM synthesized the first half-Möbius molecule using quantum computing
   techniques. This milestone opens new paths in molecular engineering.
   https://www.scientificamerican.com/article/ibm-scientists-unveil-...

...
```

## Cost

~$0.01-0.05/day using GPT-4o-mini (a single API call with ~6K tokens per run). GitHub Actions is free for public repos.

## Dependencies

- `feedparser` — RSS parsing for Quanta Magazine
- `httpx` — HTTP client for Scientific American
- `beautifulsoup4` — HTML parsing
- `openai` — GPT-4o-mini summarization
- `python-dotenv` — Environment variable loading

Dev: `pytest`, `respx`

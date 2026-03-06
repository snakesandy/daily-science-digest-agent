# Daily Science Digest Agent

A daily morning digest agent that selects the 10 best new articles focused on **innovation in math and science** from Quanta Magazine, Nature, and arXiv. Summarizes them using OpenAI GPT-4o-mini and delivers clickable links with summaries to Telegram every morning at 6:00 AM EST.

## How It Works

```
RSS Fetch → Deduplicate → Filter → Rank → Summarize → Deliver
```

1. **Fetch** articles from Quanta Magazine (RSS), Nature (RSS), and arXiv (RSS — math, physics, cs.AI, cs.LG)
2. **Deduplicate** against previously seen articles (JSON file store, 30-day retention) — ensures no repeat articles day to day
3. **Filter** out podcasts, videos, retractions, and multimedia content
4. **Rank** by topic relevance (math, physics, AI, science innovation) + recency + priority keywords + source quality
5. **Summarize** the top 10 via OpenAI GPT-4o-mini (1-2 sentences: what's new + why it matters)
6. **Deliver** to console and Telegram

## Sources

| Source | Method | Strength |
|--------|--------|----------|
| **Quanta Magazine** | RSS feed | Deep, curated math/physics/CS journalism |
| **Nature** | RSS feed | Broad cutting-edge science research |
| **arXiv** | RSS feeds (math, physics, cs.AI, cs.LG) | Latest preprints and breakthroughs |

Curated editorial sources (Quanta, Nature) are ranked higher than raw preprints (arXiv) to ensure the digest favors accessible, high-impact articles. arXiv papers still appear when they are highly relevant.

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
│   │   ├── quanta.py            # Quanta Magazine RSS
│   │   ├── nature.py            # Nature RSS
│   │   └── arxiv.py             # arXiv RSS (multiple categories)
│   ├── filter.py                # Podcast/video exclusion + topic scoring
│   ├── ranker.py                # Score + select top 10
│   ├── summarizer.py            # OpenAI GPT-4o-mini summarization
│   ├── dedup.py                 # JSON-file dedup store
│   └── output.py                # ConsoleOutput + TelegramOutput
├── tests/                       # 26 tests, all mocked (no API keys needed)
│   ├── test_filter.py
│   ├── test_dedup.py
│   ├── test_ranker.py
│   ├── test_sources.py
│   ├── test_integration.py
│   └── fixtures/
│       ├── quanta_feed.xml
│       ├── nature_feed.xml
│       └── arxiv_feed.xml
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
chmod +x run_digest.sh

# Add to crontab (6am EST = 11:00 UTC)
crontab -e
# Add this line:
0 11 * * * /path/to/daily-science-digest-agent/run_digest.sh
```

Note: local cron requires your machine to be awake at the scheduled time.

## Configuration

### Topic Priorities

The agent prioritizes articles about innovation in:
- **Mathematics**: algebra, geometry, topology, number theory, proofs, conjectures, optimization, cryptography
- **Physics**: quantum, particle physics, cosmology, astrophysics, black holes, superconductors, fusion, photonics
- **AI/CS**: artificial intelligence, machine learning, deep learning, neural networks, algorithms
- **Broader science**: genomics, CRISPR, synthetic biology, nanotechnology, materials science, semiconductors

These keywords are defined in `src/digest/filter.py` and can be modified.

### Ranking

Articles are scored by:
- **Topic relevance** (0-10): keyword matches in title, description, and categories
- **Innovation signal** (0-10): keywords like "breakthrough", "discovery", "novel", "first", "solved", "proves"
- **Recency bonus** (0-3): newer articles score higher
- **Source quality bonus**: Quanta (+8), Nature (+6), arXiv (capped at 10 total)

This ensures curated editorial content surfaces above raw preprints, while still including exceptional arXiv papers.

### Fetch Window

Articles from the last 7 days are fetched to ensure all sources are well represented. The dedup store ensures you never see the same article twice across runs.

## Output Example

```
=== Daily Science Digest — March 6, 2026 ===

1) Can the Most Abstract Math Make the World a Better Place?
   Applied category theory may offer mathematical tools for addressing
   environmental challenges, potentially leading to innovative solutions
   for sustainability.
   https://www.quantamagazine.org/can-the-most-abstract-math-...

2) AI can write genomes — how long until it creates synthetic life?
   AI models can now generate complete genome sequences, raising questions
   about the feasibility and ethics of creating synthetic organisms.
   https://www.nature.com/articles/d41586-026-00681-y

3) First 'half Möbius' carbon chain wows chemists
   Scientists synthesized the first half-Möbius carbon structure, a
   topological milestone in molecular chemistry with potential materials
   science applications.
   https://www.nature.com/articles/d41586-026-00682-x

...
```

## Cost

~$0.01-0.05/day using GPT-4o-mini (a single API call with ~6K tokens per run). GitHub Actions is free for public repos.

## Dependencies

- `feedparser` — RSS parsing for Quanta, Nature, and arXiv
- `httpx` — HTTP client (used by Telegram output)
- `beautifulsoup4` — HTML parsing (Scientific American fallback)
- `openai` — GPT-4o-mini summarization
- `python-dotenv` — Environment variable loading

Dev: `pytest`, `respx`

# Daily Science Digest Agent

A daily morning digest agent that selects the 10 best new articles focused on **algorithms, mathematics, and AI/ML innovation** from Quanta Magazine, Nature, and arXiv. Summarizes them using OpenAI GPT-4o-mini and delivers clickable links with summaries to Telegram every morning at 6:00 AM EST.

## How It Works

```
RSS Fetch → Deduplicate → Filter → Rank → Summarize → Deliver
```

1. **Fetch** articles from Quanta Magazine (RSS), Nature (RSS), and arXiv (RSS — math, physics, cs.AI, cs.LG)
2. **Deduplicate** against previously seen articles (JSON file store, 30-day retention) — ensures no repeat articles day to day
3. **Filter** out podcasts/videos/retractions, require minimum topic relevance, penalize off-topic content (biology, chemistry, medicine, politics)
4. **Rank** by topic relevance + innovation signal + recency + source quality
5. **Summarize** the top 10 via OpenAI GPT-4o-mini (1-2 sentences: what's new + why it matters)
6. **Deliver** to console and Telegram

## Sources

| Source | Method | Bonus | Strength |
|--------|--------|-------|----------|
| **Quanta Magazine** | RSS feed | +8 | Deep, curated math/physics/CS journalism |
| **Nature** | RSS feed | +3 | Cutting-edge research (filtered to math/CS/AI) |
| **arXiv** | RSS feeds (math, physics, cs.AI, cs.LG) | capped at 10 | Latest preprints in target fields |

Curated editorial sources (Quanta, Nature) are ranked higher than raw preprints (arXiv) to ensure the digest favors accessible, high-impact articles. arXiv papers still appear when highly relevant. Note: arXiv RSS feeds are empty on weekends.

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
│   ├── filter.py                # Topic filtering + off-topic penalty + relevance gate
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

The workflow and secrets are configured on the **snakesandy** GitHub account:
- Repo: `https://github.com/snakesandy/daily-science-digest-agent`
- Secrets already set: `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- Workflow runs successfully (tested manually)

You can trigger a run manually from the Actions tab using the "Run workflow" button.

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

### Topic Focus

The agent is tightly focused on **algorithms, mathematics, and AI/ML innovation**. Articles must score > 0 on topic relevance to be included.

**On-topic keywords** (defined in `src/digest/filter.py`):
- **Mathematics**: algebra, geometry, topology, number theory, proofs, conjectures, optimization, cryptography, combinatorics, graph theory, category theory
- **Algorithms & CS**: algorithm, computation, complexity, NP-hard, data structures, solvers, approximation
- **AI/ML**: machine learning, deep learning, neural networks, LLMs, transformers, reinforcement learning, generative models, computer vision, NLP, reasoning
- **Quantum computing**: quantum algorithm, quantum computing, qubit

**Off-topic penalties** (-2 per keyword hit): biology, chemistry, medicine, ecology, politics, nutrition, surgery, etc. This prevents Nature's biology-heavy content from dominating.

### Ranking

Articles are scored by:
- **Topic relevance** (0-10): keyword matches in title, description, and categories
- **Innovation signal**: keywords like "breakthrough", "discovery", "solved", "proves", "outperforms" (+1.5 each)
- **Off-topic penalty**: biology/chemistry/medicine/politics keywords (-2.0 each)
- **Recency bonus** (0-3): newer articles score higher (gentle decay over 7 days)
- **Source quality bonus**: Quanta (+8), Nature (+3), arXiv (capped at 10 total)

### Fetch Window

Articles from the last 7 days are fetched. The dedup store (30-day retention) ensures you never see the same article twice.

## Current State & Known Issues

### Working
- All 3 sources fetch correctly (Quanta, Nature, arXiv)
- Telegram delivery works (bot: "Best Articles")
- GitHub Actions workflow runs successfully on `snakesandy` account
- 26 tests passing
- Dedup prevents repeat articles

### Known Issues / TODO
- **arXiv returns 0 articles on weekends** — this is expected, arXiv doesn't publish on weekends
- **Telegram bot token was exposed in conversation screenshots** — should regenerate via @BotFather `/revoke` and update `.env` + GitHub secret
- **GitHub Actions on `sandeepprabhakara` account has billing lock** — using `snakesandy` account instead
- **Old `sandeepprabhakara` repo still exists** (private) — can be deleted
- **Scoring tuning** — may need further adjustment once arXiv weekday data is available; current tuning was done on a weekend with 0 arXiv articles
- **No dedup persistence in GitHub Actions** — each run starts fresh (dedup file is not committed). On the flip side, the 7-day window + dedup means articles won't repeat within a local session, but GitHub Actions runs are stateless

### Future Ideas
- SMS/email delivery (output ABC is already set up)
- More sources (e.g., Proceedings of the National Academy of Sciences, ACM Digital Library)
- SQLite for persistent dedup across GitHub Actions runs
- User-configurable topic keywords via env var or config file

## Cost

~$0.01-0.05/day using GPT-4o-mini (a single API call with ~6K tokens per run). GitHub Actions is free for public repos.

## Dependencies

- `feedparser` — RSS parsing for Quanta, Nature, and arXiv
- `httpx` — HTTP client (Telegram output + Scientific American fallback)
- `beautifulsoup4` — HTML parsing
- `openai` — GPT-4o-mini summarization
- `python-dotenv` — Environment variable loading

Dev: `pytest`, `respx`

## Accounts & Infrastructure

| Service | Account | Notes |
|---------|---------|-------|
| GitHub | `snakesandy` | Public repo, Actions workflow, secrets configured |
| GitHub (old) | `sandeepprabhakara` | Billing locked, not used |
| OpenAI | — | API key in `.env` and GitHub Secrets |
| Telegram | Bot: "Best Articles" | Token needs regeneration (exposed in screenshots) |
| Telegram | Chat ID: user's personal chat | Messages delivered here |

# Goal
Build a daily morning digest agent that selects the 10 best NEW articles from:
- Scientific American
- Quanta Magazine
It sends clickable links with a 1–2 sentence summary each morning.

# Preferences
- Prioritize: new discoveries, inventions, implications
- Topics: AI, mathematics, physics
- Exclude: podcasts, videos (plain readable articles only)

# Output format
Return a numbered list:
1) Title
   1–2 sentence summary focused on: what is new + why it matters
   Link

# Non-goals (for MVP)
- No user accounts
- No payments
- No web UI

# Tech constraints
- Let Claude choose architecture, but keep it simple and inexpensive.
- Provide a local dev run command.
- Provide tests or a verification command.
- Keep secrets in environment variables, never committed.

# Definition of done
- Running locally produces a digest for "today"
- Dedupes articles
- Filters out podcasts/videos reliably
- Produces exactly 10 items (or fewer with explanation if the sources are empty)

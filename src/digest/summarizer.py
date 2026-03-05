from __future__ import annotations

from openai import OpenAI

from digest.models import Article

SYSTEM_PROMPT = (
    "You are a science news summarizer. For each article below, write exactly "
    "1-2 sentences: (1) what is new or discovered, (2) why it matters. "
    "Be specific and concise. Return your response as a numbered list matching "
    "the input numbering. Each item should be just the summary text, no title."
)


def summarize_articles(articles: list[Article], api_key: str) -> list[Article]:
    if not articles:
        return articles

    user_prompt = "\n\n".join(
        f"{i+1}. Title: {a.title}\n   Description: {a.description}\n   URL: {a.url}"
        for i, a in enumerate(articles)
    )

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=2048,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        _parse_summaries(response.choices[0].message.content, articles)
    except Exception as e:
        print(f"Warning: Summarization failed ({e}), using description fallback.")
        for a in articles:
            if not a.summary:
                a.summary = _fallback_summary(a.description)

    return articles


def _parse_summaries(text: str, articles: list[Article]) -> None:
    lines = text.strip().split("\n")
    current_num = 0
    current_text = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Check if line starts with a number like "1." or "1)"
        for sep in [".", ")", ":"]:
            prefix = f"{current_num + 1}{sep}"
            if stripped.startswith(prefix):
                # Save previous
                if current_num > 0 and current_num <= len(articles):
                    articles[current_num - 1].summary = " ".join(current_text).strip()
                current_num += 1
                current_text = [stripped[len(prefix):].strip()]
                break
        else:
            current_text.append(stripped)

    # Save last
    if current_num > 0 and current_num <= len(articles):
        articles[current_num - 1].summary = " ".join(current_text).strip()

    # Fallback for any that didn't get parsed
    for a in articles:
        if not a.summary:
            a.summary = _fallback_summary(a.description)


def _fallback_summary(description: str) -> str:
    if not description:
        return "No summary available."
    sentences = description.replace("\n", " ").split(". ")
    return ". ".join(sentences[:2]).strip().rstrip(".") + "."

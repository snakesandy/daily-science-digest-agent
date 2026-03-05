from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

import httpx

from digest.models import Article


class DigestOutput(ABC):
    @abstractmethod
    def send(self, articles: list[Article], date: datetime) -> None:
        ...


class ConsoleOutput(DigestOutput):
    def send(self, articles: list[Article], date: datetime) -> None:
        date_str = date.strftime("%B %-d, %Y")
        print(f"\n=== Daily Science Digest — {date_str} ===\n")

        if not articles:
            print("No new articles found today.")
            return

        for i, article in enumerate(articles, 1):
            summary = article.summary or "No summary available."
            print(f"{i}) {article.title}")
            print(f"   {summary}")
            print(f"   {article.url}")
            print()

        if len(articles) < 10:
            print(f"Note: Only {len(articles)} articles found (fewer sources available today).\n")


class TelegramOutput(DigestOutput):
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, articles: list[Article], date: datetime) -> None:
        date_str = date.strftime("%B %-d, %Y")
        lines = [f"<b>Daily Science Digest — {date_str}</b>\n"]

        if not articles:
            lines.append("No new articles found today.")
        else:
            for i, article in enumerate(articles, 1):
                summary = article.summary or "No summary available."
                lines.append(
                    f"{i}) <b>{_escape_html(article.title)}</b>\n"
                    f"   {_escape_html(summary)}\n"
                    f"   <a href=\"{article.url}\">Read</a>"
                )

            if len(articles) < 10:
                lines.append(f"\n<i>Only {len(articles)} articles found today.</i>")

        message = "\n\n".join(lines)

        # Telegram has a 4096 char limit per message
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            resp = httpx.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=30,
            )
            resp.raise_for_status()
            print("Telegram message sent successfully.")
        except Exception as e:
            print(f"Warning: Failed to send Telegram message: {e}")


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

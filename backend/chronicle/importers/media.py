"""News coverage of one event as `media` story transcripts (concept §9.4, R3).

Each outlet gets a story of its own, because completion per outlet needs a lattice built from that
outlet's claims alone (WP-054 compares them). Every paragraph of an article becomes an utterance
spoken by the outlet; the ingester turns what it states into claims by the outlet (WP-052)."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from django.utils.text import slugify

BLANK_LINES = re.compile(r"\n\s*\n")
SOURCE_FIELDS = ("outlet", "author", "published_at", "url")


class ArticleCollectionError(ValueError):
    pass


@dataclass(frozen=True)
class Passage:
    text: str
    source: dict[str, str]  # outlet, author, published_at, url


@dataclass
class Outlet:
    slug: str
    name: str
    passages: list[Passage] = field(default_factory=list)


@dataclass(frozen=True)
class ArticleCollection:
    event: str
    title: str
    outlets: dict[str, Outlet]  # by slug, in order of first publication

    @property
    def passage_count(self) -> int:
        return sum(len(outlet.passages) for outlet in self.outlets.values())


def parse_articles(document: Mapping[str, Any]) -> ArticleCollection:
    articles = [
        checked_article(number, article) for number, article in enumerate(document["articles"], start=1)
    ]
    outlets: dict[str, Outlet] = {}
    for article in sorted(articles, key=lambda article: article["published_at"]):
        slug = slugify(article["outlet"])
        outlet = outlets.setdefault(slug, Outlet(slug=slug, name=article["outlet"]))
        source = {key: article[key] for key in SOURCE_FIELDS}
        outlet.passages += [
            Passage(text=paragraph, source=source) for paragraph in paragraphs(article["text"])
        ]
    return ArticleCollection(event=document["event"], title=document["title"], outlets=outlets)


def checked_article(number: int, article: Mapping[str, Any]) -> dict[str, str]:
    missing = [key for key in ("outlet", "text") if not article.get(key)]
    if missing:
        raise ArticleCollectionError(f"article {number}: missing '{missing[0]}'")
    return {key: text_of(article.get(key, "")) for key in (*SOURCE_FIELDS, "text")}


def text_of(value: object) -> str:
    """YAML reads unquoted timestamps as datetimes; they are kept in ISO format."""
    return value.isoformat() if isinstance(value, datetime) else str(value)


def paragraphs(text: str) -> list[str]:
    return [" ".join(block.split()) for block in BLANK_LINES.split(text) if block.strip()]

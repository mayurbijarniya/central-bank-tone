"""New speeches from central banks that publish them as RSS feeds the same day.

The BIS archive runs a few months behind. These five banks post each speech
on their own site the day it is given, so `cbtone update` reads their feeds
and keeps whatever is newer than the archive. When the BIS later publishes the
same speeches, the archive version is used instead.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

import polars as pl

from cbtone import paths

FEEDS = {
    "US": "https://www.federalreserve.gov/feeds/speeches.xml",
    "XM": "https://www.ecb.europa.eu/rss/press.html",
    "GB": "https://www.bankofengland.co.uk/rss/speeches",
    "CA": "https://www.bankofcanada.ca/content_type/speeches/feed/",
    "AU": "https://www.rba.gov.au/rss/rss-cb-speeches.xml",
}

# The ECB feed also carries press releases and interviews; speeches live under /press/key/.
# The Bank of Canada's feed also carries press conference videos under /multimedia/.
SPEECH_LINK = {
    "XM": re.compile(r"/press/key/.*\.html$"),
    "CA": re.compile(r"bankofcanada\.ca/\d{4}/\d{2}/"),
}

USER_AGENT = "Mozilla/5.0 (cbtone research)"
MIN_WORDS = 300


def speech_id(url: str) -> str:
    """A stable id for a feed speech, from its address."""
    return "feed-" + hashlib.sha1(url.encode()).hexdigest()[:12]


def get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _date(text: str) -> date | None:
    text = (text or "").strip()
    try:
        return parsedate_to_datetime(text).date()
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


def items(feed: bytes) -> list[dict]:
    """Title, link and date of every item in an RSS or RDF feed."""
    out = []
    for item in ET.fromstring(feed).iter():
        if _local(item.tag) not in ("item", "entry"):
            continue
        fields = {_local(child.tag): (child.text or "").strip() for child in item}
        published = _date(fields.get("pubDate") or fields.get("date") or "")
        if fields.get("link") and published:
            out.append({
                "title": html.unescape(fields.get("title", "")).strip(),
                "url": fields["link"],
                "date": published,
            })
    return out


class _Paragraphs(HTMLParser):
    """Collects the text of <p> elements, which hold the body of a speech page."""

    def __init__(self) -> None:
        super().__init__()
        self.paragraphs: list[str] = []
        self._depth = 0
        self._current: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer", "header"):
            self._skip += 1
        elif tag == "p":
            self._depth += 1
            self._current = []

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer", "header") and self._skip:
            self._skip -= 1
        elif tag == "p" and self._depth:
            self._depth -= 1
            text = re.sub(r"\s+", " ", "".join(self._current)).strip()
            if text:
                self.paragraphs.append(text)

    def handle_data(self, data):
        if self._depth and not self._skip:
            self._current.append(data)


def page_text(page: bytes) -> str:
    parser = _Paragraphs()
    parser.feed(page.decode("utf-8", errors="replace"))
    return "\n\n".join(p for p in parser.paragraphs if len(p.split()) >= 8)


def fetch(after: date) -> list[dict]:
    """Speeches newer than `after` from every feed, saved under data/raw/feeds."""
    found = []
    for area, url in FEEDS.items():
        try:
            entries = items(get(url))
        except (urllib.error.URLError, ET.ParseError, TimeoutError):
            continue
        pattern = SPEECH_LINK.get(area)
        for entry in entries:
            if entry["date"] <= after or (pattern and not pattern.search(entry["url"])):
                continue
            slug = re.sub(r"[^a-z0-9]+", "-", entry["url"].lower()).strip("-")[-90:]
            target = paths.RAW_FEEDS / area / f"{slug}.json"
            if target.exists():
                found.append(json.loads(target.read_text()))
                continue
            try:
                text = page_text(get(entry["url"]))
            except (urllib.error.URLError, TimeoutError):
                continue
            if len(text.split()) < MIN_WORDS:
                continue
            record = {**entry, "date": entry["date"].isoformat(), "area": area, "text": text}
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(record, ensure_ascii=False))
            found.append(record)
    return found


def saved() -> pl.DataFrame:
    """Every speech saved from the feeds so far."""
    records = [json.loads(p.read_text()) for p in sorted(paths.RAW_FEEDS.glob("*/*.json"))]
    schema = {"title": pl.Utf8, "url": pl.Utf8, "date": pl.Utf8, "area": pl.Utf8, "text": pl.Utf8}
    return pl.DataFrame(records, schema=schema).with_columns(pl.col("date").str.to_date())

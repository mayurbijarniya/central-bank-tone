"""Download the BIS files this project uses.

The BIS publishes every central banker's speech it collects as one CSV per
year, and the policy rates of about 40 central banks as one bulk file. The
server sometimes closes long transfers early, so each file is resumed until it
arrives whole.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

from cbtone import paths

SPEECHES_URL = "https://www.bis.org/pages/download-central-bankers-speeches/speeches-{year}.zip"
RATES_URL = "https://data.bis.org/static/bulk/WS_CBPOL_csv_flat.zip"
PRICES_URL = "https://data.bis.org/static/bulk/WS_LONG_CPI_csv_flat.zip"

FIRST_YEAR = 1996
ATTEMPTS = 20
PAUSE_SECONDS = 2.0
USER_AGENT = "cbtone research (+https://github.com/mayurbijarniya/central-bank-tone)"


def is_whole(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            return archive.testzip() is None
    except (zipfile.BadZipFile, OSError):
        return False


def fetch(url: str, target: Path, refresh: bool = False) -> Path:
    """Download `url` to `target`, resuming partial transfers."""
    if target.exists() and not refresh and is_whole(target):
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    partial.unlink(missing_ok=True)

    for _ in range(ATTEMPTS):
        offset = partial.stat().st_size if partial.exists() else 0
        headers = {"User-Agent": USER_AGENT}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                # A server that ignores the range starts again from the beginning.
                mode = "ab" if offset and response.status == 206 else "wb"
                with partial.open(mode) as out:
                    while chunk := response.read(1 << 16):
                        out.write(chunk)
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        if is_whole(partial):
            partial.replace(target)
            return target
        time.sleep(PAUSE_SECONDS)
    raise RuntimeError(f"could not download {url} after {ATTEMPTS} attempts")


def run(last_year: int | None = None, refresh_recent: bool = False) -> list[Path]:
    """Fetch every yearly speech file, the policy rates and consumer prices.

    Past years do not change, so only the current year and the rate file are
    fetched again when `refresh_recent` is set.
    """
    last_year = last_year or date.today().year
    fetched = []
    for year in range(FIRST_YEAR, last_year + 1):
        target = paths.RAW_SPEECHES / f"speeches-{year}.zip"
        refresh = refresh_recent and year >= last_year - 1
        fetched.append(fetch(SPEECHES_URL.format(year=year), target, refresh))
    fetched.append(fetch(RATES_URL, paths.RAW_RATES, refresh_recent))
    fetched.append(fetch(PRICES_URL, paths.RAW_PRICES, refresh_recent))
    return fetched

#!/usr/bin/env python3
"""
UniBE Fitnessraum Crowd-Monitor Crawler

Ziel:
- alle Runs nachvollziehbar loggen
- auch Fehler und "keine Daten" sichtbar machen
- Trigger (schedule vs. workflow_dispatch) festhalten
- Zeitstempel konsistent in UTC speichern
"""

from __future__ import annotations

import csv
import os
import re
from datetime import datetime, timezone
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup

URL = "https://www.zssw.unibe.ch/usp/zms/templates/crowdmonitoring/_display-spaces-zssw.php"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-CH,de;q=0.9",
    "Referer": "https://sport.unibe.ch/sportangebot/fitnessraeume/index_ger.html",
}
CSV_FILE = "crowd_data.csv"
GYM_NAMES = ["ZSSw", "vonRoll"]
NUMBER_PATTERN = re.compile(r"(\d+)\s*von\s*(\d+)", re.IGNORECASE)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def csv_header() -> List[str]:
    return [
        "timestamp_utc",
        "weekday_utc",
        "hour_utc",
        "minute_utc",
        "trigger",
        "run_id",
        "gym",
        "current",
        "maximum",
        "percent",
        "status",
        "message",
    ]


def ensure_csv_exists() -> None:
    if not os.path.isfile(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(csv_header())


def append_row(row: List[object]) -> None:
    ensure_csv_exists()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


def base_row(now: datetime) -> List[object]:
    return [
        iso_utc(now),
        now.strftime("%A"),
        now.hour,
        now.minute,
        os.getenv("TRIGGER", os.getenv("GITHUB_EVENT_NAME", "unknown")),
        os.getenv("RUN_ID", os.getenv("GITHUB_RUN_ID", "unknown")),
    ]


def fetch_html() -> str:
    response = requests.get(URL, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return response.text


def extract_results(html: str) -> List[Tuple[str, int, int, float, str]]:
    soup = BeautifulSoup(html, "html.parser")

    elements = soup.find_all("div", class_="go-stop-display_footer")
    if not elements:
        elements = soup.select(".ajax-updatable_message")

    results: List[Tuple[str, int, int, float, str]] = []
    for idx, element in enumerate(elements):
        text = element.get_text(" ", strip=True)
        match = NUMBER_PATTERN.search(text)
        if not match:
            continue

        current = int(match.group(1))
        maximum = int(match.group(2))
        percent = round((current / maximum) * 100, 1) if maximum else 0.0
        gym_name = GYM_NAMES[idx] if idx < len(GYM_NAMES) else f"Gym_{idx + 1}"
        results.append((gym_name, current, maximum, percent, text))

    return results


def main() -> None:
    now = utc_now()
    prefix = base_row(now)
    print(f"[{iso_utc(now)}] Starte Crawl...")

    try:
        html = fetch_html()
        print(f"HTTP erfolgreich, Antwortlänge: {len(html)} bytes")

        results = extract_results(html)
        if not results:
            append_row(prefix + ["SYSTEM", "", "", "", "no_data", "No parsable occupancy found"])
            print("Keine parsebaren Belegungsdaten gefunden.")
            return

        for gym_name, current, maximum, percent, raw_text in results:
            append_row(prefix + [gym_name, current, maximum, percent, "ok", raw_text])
            print(f"{gym_name}: {current}/{maximum} = {percent}%")

        print(f"Gespeichert in {CSV_FILE}")

    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        append_row(prefix + ["SYSTEM", "", "", "", "http_error", f"HTTP status {status_code}: {exc}"])
        print(f"HTTP-Fehler: {exc}")
        raise
    except requests.RequestException as exc:
        append_row(prefix + ["SYSTEM", "", "", "", "request_error", str(exc)])
        print(f"Request-Fehler: {exc}")
        raise
    except Exception as exc:
        append_row(prefix + ["SYSTEM", "", "", "", "error", str(exc)])
        print(f"Allgemeiner Fehler: {exc}")
        raise


if __name__ == "__main__":
    main()

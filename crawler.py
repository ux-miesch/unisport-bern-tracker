#!/usr/bin/env python3
"""
UniBE Fitnessraum Crowd-Monitor Crawler
Liest "X von 80" aus .go-stop-display_footer und speichert in CSV.
"""

import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime

URL = "https://sport.unibe.ch/sportangebot/fitnessraeume/index_ger.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-CH,de;q=0.9",
    "Cache-Control": "no-cache",
}
CSV_FILE = "crowd_data.csv"
GYM_NAMES = ["ZSSw", "vonRoll"]


def ensure_csv_exists():
    if not os.path.isfile(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                "timestamp", "weekday", "hour", "minute",
                "gym", "current", "maximum", "percent"
            ])


def main():
    now = datetime.now()
    print(f"[{now.strftime('%Y-%m-%d %H:%M')}] Crawle UniBE Crowd-Monitor...")

    try:
        resp = requests.get(URL, headers=HEADERS, timeout=20)
        print(f"  HTTP Status: {resp.status_code} | Grösse: {len(resp.text)} bytes")

        soup = BeautifulSoup(resp.text, "html.parser")

        # Zielklasse: go-stop-display_footer
        elements = soup.find_all("div", class_="go-stop-display_footer")
        print(f"  go-stop-display_footer gefunden: {len(elements)}")
        for el in elements:
            print(f"    -> '{el.get_text(strip=True)}'")

        results = []
        for el in elements:
            text = el.get_text(strip=True)
            if " von " in text:
                parts = text.split(" von ")
                try:
                    current = int(parts[0].strip())
                    maximum = int(parts[1].strip())
                    percent = round((current / maximum) * 100, 1)
                    results.append((current, maximum, percent))
                except ValueError:
                    print(f"  Konnte nicht parsen: '{text}'")

        if not results:
            print("  Keine Daten gefunden — Gym geschlossen oder HTML geändert.")
        else:
            ensure_csv_exists()
            with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for i, (current, maximum, percent) in enumerate(results):
                    name = GYM_NAMES[i] if i < len(GYM_NAMES) else f"Gym_{i+1}"
                    writer.writerow([
                        now.isoformat(),
                        now.strftime("%A"),
                        now.hour,
                        now.minute,
                        name,
                        current,
                        maximum,
                        percent,
                    ])
                    print(f"  {name}: {current}/{maximum} = {percent}%")
            print(f"  Gespeichert in {CSV_FILE}")

    except Exception as e:
        print(f"  FEHLER: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ensure_csv_exists()


if __name__ == "__main__":
    main()

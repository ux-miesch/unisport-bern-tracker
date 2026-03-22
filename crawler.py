#!/usr/bin/env python3
"""
UniBE Fitnessraum Crowd-Monitor Crawler
Liest die aktuelle Auslastung von sport.unibe.ch und speichert sie als CSV.
"""

import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime
import json

URL = "https://sport.unibe.ch/sportangebot/fitnessraeume/index_ger.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "de-CH,de;q=0.9",
}
CSV_FILE = "crowd_data.csv"


def parse_value(text):
    """Parst '14 von 80' -> (14, 80, 17.5)"""
    text = text.strip()
    parts = text.split(" von ")
    if len(parts) == 2:
        try:
            current = int(parts[0].strip())
            maximum = int(parts[1].strip())
            percent = round((current / maximum) * 100, 1) if maximum > 0 else 0
            return current, maximum, percent
        except ValueError:
            pass
    return None, None, None


def fetch_crowd_data():
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Alle Crowd-Monitor Elemente finden
    elements = soup.find_all(class_="ajax-updatable_message")

    results = []
    for el in elements:
        text = el.get_text(strip=True)
        if " von " in text:
            current, maximum, percent = parse_value(text)
            if current is not None:
                results.append({
                    "text": text,
                    "current": current,
                    "maximum": maximum,
                    "percent": percent,
                })

    return results


def save_to_csv(data, timestamp):
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp", "weekday", "hour", "minute",
                "gym", "current", "maximum", "percent"
            ])

        gym_names = ["ZSSw", "vonRoll"]
        for i, entry in enumerate(data):
            name = gym_names[i] if i < len(gym_names) else f"Gym_{i+1}"
            writer.writerow([
                timestamp.isoformat(),
                timestamp.strftime("%A"),
                timestamp.hour,
                timestamp.minute,
                name,
                entry["current"],
                entry["maximum"],
                entry["percent"],
            ])


def main():
    now = datetime.now()
    print(f"[{now.strftime('%Y-%m-%d %H:%M')}] Crawle UniBE Crowd-Monitor...")

    try:
        data = fetch_crowd_data()
        if not data:
            print("  WARNUNG: Keine Crowd-Daten gefunden (Gym geschlossen oder HTML geändert)")
            return

        save_to_csv(data, now)

        for i, entry in enumerate(data):
            gym = ["ZSSw", "vonRoll"][i] if i < 2 else f"Gym {i+1}"
            print(f"  {gym}: {entry['current']}/{entry['maximum']} ({entry['percent']}%)")

        print(f"  Gespeichert in {CSV_FILE}")

    except requests.RequestException as e:
        print(f"  FEHLER beim Abrufen: {e}")
    except Exception as e:
        print(f"  FEHLER: {e}")
        raise


if __name__ == "__main__":
    main()

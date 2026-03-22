#!/usr/bin/env python3
"""
UniBE Fitnessraum Crowd-Monitor Crawler
"""

import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime

URL = "https://sport.unibe.ch/sportangebot/fitnessraeume/index_ger.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "de-CH,de;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
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
    print(f"  Fetching: {URL}")
    resp = requests.get(URL, headers=HEADERS, timeout=20)
    print(f"  HTTP Status: {resp.status_code}")
    print(f"  Response size: {len(resp.text)} bytes")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Debug: alle Klassen suchen die "ajax" enthalten
    ajax_els = soup.find_all(class_=lambda c: c and "ajax" in c)
    print(f"  Gefundene ajax-Elemente: {len(ajax_els)}")
    for el in ajax_els:
        print(f"    -> [{el.get('class')}] Text: '{el.get_text(strip=True)}'")

    # Suche nach "von" im ganzen Dokument als Fallback
    all_von = [el for el in soup.find_all(string=lambda t: t and " von " in t)]
    print(f"  Elemente mit ' von ': {len(all_von)}")
    for t in all_von[:5]:
        print(f"    -> '{t.strip()}'")

    # Crowd-Monitor Elemente
    results = []
    elements = soup.find_all(class_="ajax-updatable_message")
    print(f"  ajax-updatable_message Elemente: {len(elements)}")

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
            print("  WARNUNG: Keine Crowd-Daten gefunden.")
            print("  Schreibe leere CSV damit Git-Step nicht fehlschlägt...")
            # Leere CSV erstellen damit der Workflow nicht abbricht
            if not os.path.isfile(CSV_FILE):
                with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "timestamp", "weekday", "hour", "minute",
                        "gym", "current", "maximum", "percent"
                    ])
            return

        save_to_csv(data, now)
        for i, entry in enumerate(data):
            gym = ["ZSSw", "vonRoll"][i] if i < 2 else f"Gym {i+1}"
            print(f"  {gym}: {entry['current']}/{entry['maximum']} ({entry['percent']}%)")
        print(f"  Gespeichert in {CSV_FILE}")

    except Exception as e:
        print(f"  FEHLER: {e}")
        import traceback
        traceback.print_exc()
        # CSV trotzdem erstellen
        if not os.path.isfile(CSV_FILE):
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    "timestamp", "weekday", "hour", "minute",
                    "gym", "current", "maximum", "percent"
                ])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
UniBE Fitnessraum Crowd-Monitor Crawler
"""

import requests
from bs4 import BeautifulSoup
import csv
import os
import re
from datetime import datetime

URL = "https://sport.unibe.ch/sportangebot/fitnessraeume/index_ger.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "de-CH,de;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}
CSV_FILE = "crowd_data.csv"


def fetch_crowd_data(html):
    soup = BeautifulSoup(html, "html.parser")

    # Methode 1: Klasse ajax-updatable
    elements = soup.find_all(class_="ajax-updatable")
    print(f"  ajax-updatable Elemente: {len(elements)}")
    for el in elements:
        print(f"    -> '{el.get_text(strip=True)}'")

    # Methode 2: Klasse go-stop-display_footer
    elements2 = soup.find_all(class_="go-stop-display_footer")
    print(f"  go-stop-display_footer Elemente: {len(elements2)}")
    for el in elements2:
        print(f"    -> '{el.get_text(strip=True)}'")

    # Methode 3: Regex nur auf go-stop-display_footer Kontext
    pattern = re.findall(
        r'go-stop-display_footer[^>]*>\s*(\d{1,3})\s+von\s+(\d{1,3})',
        html
    )
    print(f"  go-stop Regex Treffer: {pattern}")

    # Methode 4: Regex auf ajax-updatable Kontext  
    pattern2 = re.findall(
        r'ajax-updatable[^>]*>\s*(\d{1,3})\s+von\s+(\d{1,3})',
        html
    )
    print(f"  ajax-updatable Regex Treffer: {pattern2}")

    # Methode 5: Alle "XX von YY" wo beide Zahlen <= 200
    all_matches = re.findall(r'\b(\d{1,3})\s+von\s+(\d{1,3})\b', html)
    valid = [(a, b) for a, b in all_matches if int(a) <= int(b) <= 200]
    print(f"  Alle 'X von Y' (max 200): {valid}")

    # Beste Methode auswählen
    hits = pattern or pattern2 or valid
    results = []
    gym_names = ["ZSSw", "vonRoll"]
    for i, (cur, mx) in enumerate(hits[:2]):
        current, maximum = int(cur), int(mx)
        percent = round((current / maximum) * 100, 1) if maximum > 0 else 0
        results.append({
            "current": current, "maximum": maximum, "percent": percent
        })
        name = gym_names[i] if i < 2 else f"Gym_{i+1}"
        print(f"  {name}: {current}/{maximum} = {percent}%")

    return results


def ensure_csv_exists():
    if not os.path.isfile(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                "timestamp", "weekday", "hour", "minute",
                "gym", "current", "maximum", "percent"
            ])


def save_to_csv(data, timestamp):
    ensure_csv_exists()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
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
        resp = requests.get(URL, headers=HEADERS, timeout=20)
        print(f"  HTTP Status: {resp.status_code}")
        print(f"  Response size: {len(resp.text)} bytes")

        data = fetch_crowd_data(resp.text)

        if not data:
            print("  WARNUNG: Keine Daten gefunden (Gym geschlossen?)")
        else:
            save_to_csv(data, now)
            print(f"  Gespeichert in {CSV_FILE}")

    except Exception as e:
        print(f"  FEHLER: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ensure_csv_exists()


if __name__ == "__main__":
    main()

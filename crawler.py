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


def parse_value(text):
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

    # Methode 1: BeautifulSoup mit Klasse
    soup = BeautifulSoup(resp.text, "html.parser")
    elements = soup.find_all(class_="ajax-updatable")
    print(f"  ajax-updatable Elemente (BS4): {len(elements)}")

    # Methode 2: Direkte Regex-Suche nach "X von Y" im rohen HTML
    matches = re.findall(r'(\d+)\s+von\s+(\d+)', resp.text)
    print(f"  'X von Y' Muster im HTML: {matches}")

    # Methode 3: Suche nach go-stop-display Klasse
    go_stop = soup.find_all(class_=lambda c: c and "go-stop" in " ".join(c))
    print(f"  go-stop Elemente: {len(go_stop)}")
    for el in go_stop:
        print(f"    -> {el.get('class')} | '{el.get_text(strip=True)}'")

    # Methode 4: Alle Divs mit "von" im Text
    alle_von = [el for el in soup.find_all(True) if " von " in el.get_text()]
    print(f"  Elemente mit ' von ': {len(alle_von)}")
    for el in alle_von[:5]:
        print(f"    -> <{el.name} class='{el.get('class')}'> '{el.get_text(strip=True)[:50]}'")

    # Daten extrahieren: Regex direkt auf HTML
    results = []
    # Suche nach dem spezifischen Pattern im HTML-Kontext
    pattern = re.findall(r'ajax-updatable[^>]*>\s*(\d+)\s+von\s+(\d+)', resp.text)
    print(f"  Direkte Pattern-Suche: {pattern}")

    if pattern:
        gym_names = ["ZSSw", "vonRoll"]
        for i, (current_str, maximum_str) in enumerate(pattern):
            current = int(current_str)
            maximum = int(maximum_str)
            percent = round((current / maximum) * 100, 1) if maximum > 0 else 0
            results.append({
                "text": f"{current} von {maximum}",
                "current": current,
                "maximum": maximum,
                "percent": percent,
            })
            print(f"  Gefunden: {current} von {maximum} ({percent}%)")
    elif matches:
        # Fallback: alle "X von Y" nehmen
        gym_names = ["ZSSw", "vonRoll"]
        for i, (current_str, maximum_str) in enumerate(matches[:2]):
            current = int(current_str)
            maximum = int(maximum_str)
            percent = round((current / maximum) * 100, 1) if maximum > 0 else 0
            results.append({
                "text": f"{current} von {maximum}",
                "current": current,
                "maximum": maximum,
                "percent": percent,
            })

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
        data = fetch_crowd_data()
        if not data:
            print("  WARNUNG: Keine Daten gefunden (Gym geschlossen oder Server blockt)")
        else:
            save_to_csv(data, now)
            for i, entry in enumerate(data):
                gym = ["ZSSw", "vonRoll"][i] if i < 2 else f"Gym {i+1}"
                print(f"  {gym}: {entry['current']}/{entry['maximum']} ({entry['percent']}%)")
            print(f"  Gespeichert in {CSV_FILE}")
    except Exception as e:
        print(f"  FEHLER: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ensure_csv_exists()


if __name__ == "__main__":
    main()

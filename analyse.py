#!/usr/bin/env python3
"""
Analysiert crowd_data.csv und gibt die besten Trainingszeiten aus.
Beste Trainingszeit = niedrigste Auslastung = wenig Leute.
"""

import csv
from collections import defaultdict

CSV_FILE = "crowd_data.csv"
DAYS_DE = {
    "Monday": "Montag", "Tuesday": "Dienstag", "Wednesday": "Mittwoch",
    "Thursday": "Donnerstag", "Friday": "Freitag",
    "Saturday": "Samstag", "Sunday": "Sonntag"
}


def analyse():
    buckets = defaultdict(list)

    with open(CSV_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["gym"] != "ZSSw":
                continue
            key = (row["weekday"], int(row["hour"]))
            buckets[key].append(float(row["percent"]))

    if not buckets:
        print("Keine Daten vorhanden. Warte bis der Crawler Daten gesammelt hat.")
        return

    averages = {k: sum(v)/len(v) for k, v in buckets.items()}

    print("\n=== BESTE TRAININGSZEITEN (ZSSw) — niedrigste Auslastung zuerst ===")
    print(f"{'Tag':<12} {'Uhrzeit':<10} {'Ø Auslastung'}")
    print("-" * 40)

    for (day, hour), avg in sorted(averages.items(), key=lambda x: x[1])[:10]:
        bar = "█" * int(avg / 5)
        print(f"{DAYS_DE.get(day, day):<12} {hour:02d}:00 Uhr   {avg:5.1f}%  {bar}")

    print("\n=== BESTER SLOT PRO WOCHENTAG ===")
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
        day_data = [(h, avg) for (d, h), avg in averages.items() if d == day]
        if not day_data:
            continue
        best_hour, best_avg = min(day_data, key=lambda x: x[1])
        print(f"{DAYS_DE.get(day, day):<12} {best_hour:02d}:00 Uhr  ({best_avg:.0f}% Auslastung)")

    print(f"\nTotal Messungen: {sum(len(v) for v in buckets.values())}")


if __name__ == "__main__":
    analyse()

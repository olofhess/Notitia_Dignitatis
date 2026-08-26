#
# Living Notitia V2
# geocode_places.py
#

from pathlib import Path
import csv
import time
import requests

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "csv" / "PlaceGazetteer.csv"
OUTPUT = ROOT / "csv" / "PlaceGazetteer.csv"

USER_AGENT = "LivingNotitia/1.0"

rows = []

with open(INPUT, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)


def lookup(place):

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": place,
        "format": "jsonv2",
        "limit": 1
    }

    headers = {
        "User-Agent": USER_AGENT
    }

    try:

        r = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=20
        )

        if r.status_code != 200:
            return None

        data = r.json()

        if not data:
            return None

        item = data[0]

        return {
            "modernName": item.get("display_name", ""),
            "latitude": item.get("lat", ""),
            "longitude": item.get("lon", ""),
            "confidence": "automatic"
        }

    except Exception:

        return None


updated = 0

for row in rows:

    if row["latitude"].strip():
        continue

    place = row["placeName"].strip()

    if not place:
        continue

    print(place)

    result = lookup(place)

    if result:

        row["modernName"] = result["modernName"]
        row["latitude"] = result["latitude"]
        row["longitude"] = result["longitude"]
        row["confidence"] = result["confidence"]

        updated += 1

    time.sleep(1)


with open(OUTPUT, "w", newline="", encoding="utf-8") as f:

    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)


print()
print("Living Notitia V2")
print("geocode_places.py")
print()
print("Places :", len(rows))
print("Updated:", updated)
print("Output :", OUTPUT)

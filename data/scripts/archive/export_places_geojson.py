#
# Living Notitia V2
# export_places_geojson.py
#

from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "PlaceProvince.csv"
OUTPUT = ROOT / "data" / "places.geojson"

print()
print("Living Notitia V2")
print("export_places_geojson.py")
print()

features = []
count = 0

with open(INPUT, encoding="utf-8") as f:

    reader = csv.DictReader(f)

    for row in reader:

        lat = row["latitude"].strip()
        lon = row["longitude"].strip()

        if not lat or not lon:
            continue

        lat = float(lat.replace(",", "."))
        lon = float(lon.replace(",", "."))

        feature = {

            "type": "Feature",

            "geometry": {

                "type": "Point",

                "coordinates": [
                    lon,
                    lat
                ]
            },

            "properties": {

                "placeId": row["placeId"],

                "placeName": row["placeName"],

                "chapter": row["chapter"],

                "unit": row["unit"],

                "province": row["provinceName"],

                "method": row["method"]

            }

        }

        features.append(feature)
        count += 1


geojson = {

    "type": "FeatureCollection",

    "features": features

}


with open(OUTPUT, "w", encoding="utf-8") as f:

    json.dump(
        geojson,
        f,
        indent=2,
        ensure_ascii=False
    )


print("Places :", count)
print("Output :", OUTPUT)
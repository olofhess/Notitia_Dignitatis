#
# Living Notitia V3
# analyse_missing_coordinates.py
#
from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[1]

INPUT=ROOT/"csv"/"PlaceGazetteer.csv"
OUTPUT=ROOT/"csv"/"MissingCoordinates.csv"

FIELDS=[
"placeName",
"pleiadesId",
"pleiadesName",
"featureType",
"description",
"uri"
]

rows=[]

with open(
INPUT,
newline="",
encoding="utf-8"
) as f:

    reader=csv.DictReader(f)

    for row in reader:

        if row["latitude"] and row["longitude"]:

            continue

        rows.append({

            "placeName":
                row["placeName"],

            "pleiadesId":
                row["pleiadesId"],

            "pleiadesName":
                row["pleiadesName"],

            "featureType":
                row["featureType"],

            "description":
                row["description"],

            "uri":
                row["uri"]

        })

rows.sort(
    key=lambda r:(
        r["placeName"].lower(),
        r["pleiadesId"]
    )
)

with open(
OUTPUT,
"w",
newline="",
encoding="utf-8"
) as f:

    writer=csv.DictWriter(
        f,
        fieldnames=FIELDS
    )

    writer.writeheader()

    writer.writerows(rows)

print()
print("Living Notitia V3")
print("analyse_missing_coordinates.py")
print()
print("Missing :",len(rows))
print()
print("Output :",OUTPUT)
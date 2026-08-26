#
# Living Notitia V3
# export_place_lookup.py
#

from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[1]

INPUT=ROOT/"csv"/"PlaceCanonical.csv"
OUTPUT=ROOT/"csv"/"PlaceLookup.csv"

FIELDS=[
"searchName",
"notitiaName"
]

seen=set()
rows=[]

with open(INPUT,newline="",encoding="utf-8") as f:

    reader=csv.DictReader(f)

    for row in reader:

        name=row["notitiaName"].strip()

        if not name:
            continue

        key=name.lower()

        if key in seen:
            continue

        seen.add(key)

        rows.append({

            "searchName":name,
            "notitiaName":name

        })

rows.sort(
    key=lambda r:r["searchName"].lower()
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
print("export_place_lookup.py")
print()
print("Search names :",len(rows))
print()
print("Output :",OUTPUT)
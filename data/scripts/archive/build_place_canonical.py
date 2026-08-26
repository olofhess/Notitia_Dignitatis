#
# Living Notitia V3
# build_place_canonical.py
#

from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[3]

INPUT=ROOT/"csv"/"PlaceCandidate.csv"
OUTPUT=ROOT/"csv"/"PlaceCanonical.csv"

FIELDS=[
"placeCanonicalId",
"notitiaName",
"canonicalName",
"province",
"region",
"latitude",
"longitude",
"pleiadesId",
"wikidataId",
"geonamesId",
"confidence",
"notes"
]

places={}

with open(INPUT,encoding="utf-8") as f:

    reader=csv.DictReader(f)

    for row in reader:

        if row["candidateType"]!="Place":
            continue

        name=row["placeName"].strip()

        if not name:
            continue

        key=name.lower()

        if key in places:
            continue

        places[key]=name

rows=[]

number=1

for key in sorted(places):

    rows.append({

        "placeCanonicalId":f"PLC{number:05d}",
        "notitiaName":places[key],
        "canonicalName":"",
        "province":"",
        "region":"",
        "latitude":"",
        "longitude":"",
        "pleiadesId":"",
        "wikidataId":"",
        "geonamesId":"",
        "confidence":"",
        "notes":""

    })

    number+=1

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
print("build_place_canonical.py")
print()
print("Unique places :",len(rows))
print()
print("Output :",OUTPUT)
#
# Living Notitia V3
# build_place_matches.py
#

from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[1]

CANONICAL_INPUT=ROOT/"csv"/"PlaceCanonical.csv"
PLEIADES_INPUT=ROOT/"csv"/"PleiadesName.csv"
OUTPUT=ROOT/"csv"/"PlaceMatch.csv"

FIELDS=[
"placeName",
"pleiadesId",
"pleiadesName",
"matchType"
]

canonical=[]
pleiades=[]

with open(
CANONICAL_INPUT,
encoding="utf-8"
) as f:

    canonical=list(csv.DictReader(f))

with open(
PLEIADES_INPUT,
encoding="utf-8"
) as f:

    pleiades=list(csv.DictReader(f))

index={}

for row in pleiades:

    name=row["romanized"].strip()

    if not name:
        continue

    key=name.lower()

    index.setdefault(
        key,
        []
    ).append(row)

rows=[]

for place in canonical:

    placeName=place["notitiaName"].strip()

    key=placeName.lower()

    matches=index.get(key,[])

    if matches:

        for match in matches:

            rows.append({

                "placeName":placeName,
                "pleiadesId":match["pleiadesId"],
                "pleiadesName":match["romanized"],
                "matchType":"exact"

            })

    else:

        rows.append({

            "placeName":placeName,
            "pleiadesId":"",
            "pleiadesName":"",
            "matchType":""

        })

rows.sort(
    key=lambda r:r["placeName"].lower()
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

matched=sum(
    1
    for row in rows
    if row["pleiadesId"]
)

print()
print("Living Notitia V3")
print("build_place_matches.py")
print()
print("Places  :",len(canonical))
print("Matched :",matched)
print("Output  :",OUTPUT)
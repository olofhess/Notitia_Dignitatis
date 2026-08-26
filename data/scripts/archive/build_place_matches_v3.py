#
# Living Notitia V3
# build_place_matches_v3.py
#
from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[3]

PLACE_INPUT=ROOT/"csv"/"PlaceNormalized.csv"
PLEIADES_INPUT=ROOT/"csv"/"PleiadesName.csv"
OUTPUT=ROOT/"csv"/"PlaceMatch.csv"

FIELDS=[
"placeName",
"candidate",
"rule",
"pleiadesId",
"pleiadesName",
"matchType"
]

with open(
PLACE_INPUT,
newline="",
encoding="utf-8"
) as f:

    places=list(csv.DictReader(f))

with open(
PLEIADES_INPUT,
newline="",
encoding="utf-8"
) as f:

    pleiades=list(csv.DictReader(f))

index={}

for row in pleiades:

    name=row["romanized"].strip()

    if not name:
        continue

    index.setdefault(
        name.lower(),
        []
    ).append(row)

rows=[]
seen=set()

exactCount=0
multipleCount=0
unmatchedCount=0

for place in places:

    placeName=place["placeName"].strip()

    candidate=place["candidate"].strip()

    rule=place["rule"].strip()

    matches=index.get(
        candidate.lower(),
        []
    )

    if not matches:

        unmatchedCount+=1

        continue

    if len(matches)==1:

        exactCount+=1

    else:

        multipleCount+=1

    for match in matches:

        duplicateKey=(

            placeName.lower(),
            match["pleiadesId"]

        )

        if duplicateKey in seen:

            continue

        seen.add(duplicateKey)

        rows.append({

            "placeName":placeName,
            "candidate":candidate,
            "rule":rule,
            "pleiadesId":match["pleiadesId"],
            "pleiadesName":match["romanized"],
            "matchType":"candidate"

        })

rows.sort(
    key=lambda r:(
        r["placeName"].lower(),
        r["candidate"].lower(),
        r["pleiadesName"].lower()
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

matchedCandidates=set()

for row in rows:

    matchedCandidates.add(

        (
            row["placeName"],
            row["candidate"]
        )

    )

print()
print("Living Notitia V3")
print("build_place_matches_v3.py")
print()
print("Candidates          :",len(places))
print("Matched candidates  :",len(matchedCandidates))
print("Unmatched candidates:",len(places)-len(matchedCandidates))
print("Matched rows        :",len(rows))
print("Exact matches       :",exactCount)
print("Multiple matches    :",multipleCount)
print("Unmatched lookups   :",unmatchedCount)
print()
print("Output :",OUTPUT)
#
# Living Notitia V3
# match_place_gazetteer.py
#

from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[1]

GAZETTEER=ROOT/"csv"/"PlaceGazetteer.csv"
LOOKUP=ROOT/"csv"/"PlaceLookup.csv"
OUTPUT=ROOT/"csv"/"PlaceGazetteer.csv"

lookup={}

if LOOKUP.exists():

    with open(
        LOOKUP,
        newline="",
        encoding="utf-8"
    ) as f:

        reader=csv.DictReader(f)

        for row in reader:

            lookup[
                row["notitiaName"].strip().lower()
            ]=row

rows=[]

matched=0
unmatched=0

with open(
    GAZETTEER,
    newline="",
    encoding="utf-8"
) as f:

    reader=csv.DictReader(f)

    for row in reader:

        key=row["notitiaName"].strip().lower()

        if key in lookup:

            match=lookup[key]

            row["canonicalName"]=match.get(
                "canonicalName",""
            )

            row["modernName"]=match.get(
                "modernName",""
            )

            row["province"]=match.get(
                "province",""
            )

            row["region"]=match.get(
                "region",""
            )

            row["country"]=match.get(
                "country",""
            )

            row["latitude"]=match.get(
                "latitude",""
            )

            row["longitude"]=match.get(
                "longitude",""
            )

            row["pleiadesId"]=match.get(
                "pleiadesId",""
            )

            row["wikidataId"]=match.get(
                "wikidataId",""
            )

            row["geonamesId"]=match.get(
                "geonamesId",""
            )

            row["barringtonId"]=match.get(
                "barringtonId",""
            )

            row["confidence"]="HIGH"

            row["status"]="MATCHED"

            row["matchMethod"]="LOOKUP"

            matched+=1

        else:

            row["status"]="UNMATCHED"

            row["matchMethod"]=""

            unmatched+=1

        rows.append(row)

with open(
    OUTPUT,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer=csv.DictWriter(
        f,
        fieldnames=rows[0].keys()
    )

    writer.writeheader()

    writer.writerows(rows)

print()
print("Living Notitia V3")
print("match_place_gazetteer.py")
print()
print("Matched   :",matched)
print("Unmatched :",unmatched)
print()
print("Output :",OUTPUT)
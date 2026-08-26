#
# Living Notitia V3
# build_place_context.py
#
from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[1]
PLACE_INPUT=ROOT/"csv"/"Place.csv"
GAZETTEER_INPUT=ROOT/"csv"/"PlaceGazetteer.csv"
OUTPUT=ROOT/"csv"/"PlaceContext.csv"

FIELDS=[
"contextId",
"placeId",
"placeName",
"office",
"unit",
"chapter",
"document"
]

gazetteer={}
rows=[]

with open(GAZETTEER_INPUT,newline="",encoding="utf-8") as f:
    reader=csv.DictReader(f)
    for row in reader:
        gazetteer.setdefault(row["placeName"].strip(),[]).append(row)

with open(
PLACE_INPUT,
newline="",
encoding="utf-8"
) as f:

    reader=csv.DictReader(f)

    number=1

    for place in reader:

        rows.append({

            "contextId":f"PC{number:06d}",
            "placeId":place["placeId"],
            "placeName":place["placeName"],
            "office":place["office"],
            "unit":place["unit"],
            "chapter":place["chapter"],
            "document":place["document"]

        })

        number+=1

rows.sort(key=lambda r:(r["document"],r["chapter"],r["placeName"].lower(),r["office"],r["unit"]))

with open(OUTPUT,"w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)

print()
print("Living Notitia V3")
print("build_place_context.py")
print()
print("Rows :",len(rows))
print()
print("Output :",OUTPUT)

#
# Living Notitia V3
# analyse_unmatched_candidates.py
#
from pathlib import Path
import csv
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]

CANDIDATE_INPUT=ROOT/"csv"/"PlaceCandidate.csv"
MATCH_INPUT=ROOT/"csv"/"PlaceMatch.csv"
OUTPUT=ROOT/"csv"/"UnmatchedCandidate.csv"

FIELDS=[
"placeName",
"candidate",
"candidateType",
"chapter",
"document",
"office",
"unit"
]

matched=set()

with open(
MATCH_INPUT,
newline="",
encoding="utf-8"
) as f:

    reader=csv.DictReader(f)

    for row in reader:

        matched.add(

            (
                row["placeName"].strip(),
                row["candidate"].strip()
            )

        )

rows=[]
counter=Counter()

with open(
CANDIDATE_INPUT,
newline="",
encoding="utf-8"
) as f:

    reader=csv.DictReader(f)

    for row in reader:

        key=(

            row["placeName"].strip(),
            row["candidate"].strip()

        )

        if key in matched:

            continue

        rows.append({

            "placeName":row["placeName"],
            "candidate":row["candidate"],
            "candidateType":row["candidateType"],
            "chapter":row["chapter"],
            "document":row["document"],
            "office":row["office"],
            "unit":row["unit"]

        })

        counter[row["candidateType"]]+=1

rows.sort(

    key=lambda r:(

        r["candidate"].lower(),
        r["placeName"].lower()

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
print("analyse_unmatched_candidates.py")
print()
print("Unmatched candidates :",len(rows))
print()

for key in sorted(counter):

    print(f"{key:15}{counter[key]:6}")

print()
print("Output :",OUTPUT)
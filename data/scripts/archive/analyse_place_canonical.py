#
# Living Notitia V3
# analyse_place_canonical.py
#

from pathlib import Path
import csv
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]

INPUT=ROOT/"csv"/"PlaceCanonical.csv"
OUTPUT=ROOT/"csv"/"PlaceCanonicalReport.txt"

rows=[]

with open(INPUT,encoding="utf-8") as f:

    reader=csv.DictReader(f)

    for row in reader:
        rows.append(row)

initialCounter=Counter()
suffixCounter=Counter()
wordCounter=Counter()
prefixCounter=Counter()

for row in rows:

    name=row["notitiaName"].strip()

    if not name:
        continue

    words=name.split()

    wordCounter[len(words)]+=1

    first=words[0]

    prefixCounter[first]+=1

    initialCounter[first[0].upper()]+=1

    if len(first)>=2:

        suffixCounter[first[-2:].lower()]+=1

print()
print("Living Notitia V3")
print("analyse_place_canonical.py")
print()
print("Places :",len(rows))
print()

report=[]

report.append("Living Notitia V3")
report.append("analyse_place_canonical.py")
report.append("")
report.append(f"Unique places : {len(rows)}")
report.append("")

report.append("Words per name")
report.append("--------------------------------")

for length in sorted(wordCounter):

    report.append(
        f"{length:2d} words : {wordCounter[length]:4d}"
    )

report.append("")
report.append("Initial letters")
report.append("--------------------------------")

for letter in sorted(initialCounter):

    report.append(
        f"{letter:3s} : {initialCounter[letter]:4d}"
    )

report.append("")
report.append("Common prefixes")
report.append("--------------------------------")

for prefix,count in prefixCounter.most_common(40):

    report.append(
        f"{prefix:20s}{count:4d}"
    )

report.append("")
report.append("Common suffixes")
report.append("--------------------------------")

for suffix,count in suffixCounter.most_common(40):

    report.append(
        f"{suffix:4s}{count:4d}"
    )

report.append("")
report.append("Longest names")
report.append("--------------------------------")

longest=sorted(
    rows,
    key=lambda r:len(r["notitiaName"]),
    reverse=True
)

for row in longest[:30]:

    report.append(row["notitiaName"])

report.append("")
report.append("Alphabetical list")
report.append("--------------------------------")

for row in sorted(rows,key=lambda r:r["notitiaName"].lower()):

    report.append(row["notitiaName"])

with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:

    f.write("\n".join(report))

print("Output :",OUTPUT)
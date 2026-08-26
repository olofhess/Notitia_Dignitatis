#
# Living Notitia V3
# normalize_place_names.py
#
from pathlib import Path
import csv
import re

ROOT=Path(__file__).resolve().parents[3]

INPUT=ROOT/"csv"/"PlaceCanonical.csv"
OUTPUT=ROOT/"csv"/"PlaceNormalized.csv"

FIELDS=[
"placeName",
"candidate",
"rule"
]

WORD_RULES={
"Aquileiae":"Aquileia",
"Palmira":"Palmyra",
"Singiduno":"Singidunum",
"Ravennae":"Ravenna",
"Lauriaco":"Lauriacum",
"Mediolana":"Mediolanum",
"Mogontiaco":"Mogontiacum",
"Viminacio":"Viminacium",
"Marcianopoli":"Marcianopolis",
"Maximianopoli":"Maximianopolis",
"Trapezunta":"Trapezus",
"Nicomediae":"Nicomedia",
"Antiochiae":"Antiochia",
"Damasci":"Damascus",
"Pelusio":"Pelusium",
"Copto":"Coptos",
"Memfi":"Memphis",
"Thebas":"Thebae",
"Palmira":"Palmyra"
}

ENDINGS=[
("ae","a"),
("o","um"),
("i","us"),
("am","a"),
("em","is")
]

SPLITTERS=[
" siue ",
" sive ",
" - ",
" et "
]

rows=[]
seen=set()

def add(placeName,candidate,rule):

    candidate=" ".join(candidate.split()).strip()

    candidate=candidate.strip(".,;:-()")

    if not candidate:
        return

    key=(

        placeName.lower(),
        candidate.lower()

    )

    if key in seen:
        return

    seen.add(key)

    rows.append({

        "placeName":placeName,
        "candidate":candidate,
        "rule":rule

    })

def normalize(placeName):

    candidates=[]
    seen=set()

    def add(candidate):

        candidate=" ".join(candidate.split())

        candidate=candidate.strip(" .,;:-()")

        if not candidate:
            return

        key=candidate.lower()

        if key in seen:
            return

        seen.add(key)

        candidates.append(candidate)

    add(placeName)

    text=placeName

    for splitter in SPLITTERS:

        if splitter in text:

            for part in text.split(splitter):

                add(part)

    words=text.split()

    if len(words)>1:

        add(words[0])

    for candidate in list(candidates):

        first=candidate.split()[0]

        if first in WORD_RULES:

            add(WORD_RULES[first])

        for old,new in ENDINGS:

            if first.endswith(old):

                add(first[:-len(old)]+new)

    return candidates

with open(
INPUT,
newline="",
encoding="utf-8"
) as f:

    reader=csv.DictReader(f)

    for row in reader:

        placeName=row["notitiaName"].strip()

        for candidate in normalize(placeName):

            rule="original"

            if candidate!=placeName:

                rule="generated"

            add(
                placeName,
                candidate,
                rule
            )

rows.sort(
    key=lambda r:(
        r["placeName"].lower(),
        r["candidate"].lower()
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
print("normalize_place_names.py")
print()
print("Places      :",len({r["placeName"] for r in rows}))
print("Candidates  :",len(rows))
print("Output :",OUTPUT)
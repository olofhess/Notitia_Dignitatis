#
# Living Notitia
# 06_analyse_block_types.py
#

from pathlib import Path
import csv
import re
from collections import Counter

ROOT=Path(__file__).resolve().parents[3]

INPUT=ROOT/"csv"/"Structure.csv"
OUTPUT=ROOT/"csv"/"BlockTypes.csv"

FIELDS=[
"count",
"pattern",
"example"
]

rows=[]

with open(INPUT,encoding="utf-8") as f:

    reader=csv.DictReader(f)

    for row in reader:

        if row["kind"]=="block":

            rows.append(row)

patterns=Counter()
examples={}

ROMAN=re.compile(r"^[IVXLCDM]+\b")
NUMBER=re.compile(r"\b(unus|una|unum|duo|duae|tres|quattuor|quinque|sex|septem|octo|nouem|novem|decem|undecim|duodecim|tredecim|quattuordecim|quindecim|sedecim|septendecim|duodeuiginti|uiginti|triginta|quadraginta|quinquaginta|sexaginta|LXV|XVII|VII|V|XII|XXXII|XVIII)\b",re.I)

def normalize(text):

    text=text.strip()

    text=ROMAN.sub("",text).strip()

    if text.startswith("Sub dispositione"):

        return "Sub dispositione"

    if text.startswith("Officium"):

        return "Officium"

    if text.startswith("Per "):

        return "Per"

    if text.startswith("In provincia"):

        return "In provincia"

    if text.startswith("Intra "):

        return "Intra"

    if text.startswith("In "):

        return "In"

    if text.startswith("Item "):

        return "Item"

    if text.startswith("Sub cura"):

        return "Sub cura"

    if text.startswith("Sub iurisdictione"):

        return "Sub iurisdictione"

    if text.startswith("Extenditur"):

        return "Extenditur"

    text=NUMBER.sub("",text)

    text=re.sub(r"\s+"," ",text).strip()

    return text

for row in rows:

    pattern=normalize(row["text"])

    patterns[pattern]+=1

    if pattern not in examples:

        examples[pattern]=row["text"]

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

    for pattern,count in patterns.most_common():

        writer.writerow({

            "count":count,
            "pattern":pattern,
            "example":examples[pattern]

        })

print()
print("Living Notitia")
print("06_analyse_block_types.py")
print()
print("Blocks :",len(rows))
print("Patterns :",len(patterns))
print()
print("Output :",OUTPUT)
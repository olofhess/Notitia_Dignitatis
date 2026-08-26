#
# Living Notitia
# 07_normalize_block_types.py
#

from pathlib import Path
import csv
import re

ROOT=Path(__file__).resolve().parents[3]

INPUT=ROOT/"csv"/"Structure.csv"
OUTPUT=ROOT/"csv"/"BlockType.csv"

FIELDS=[
"nodeId",
"line",
"blockType",
"blockText"
]

NUMBER=re.compile(
r"\b(unus|una|unum|duo|duae|tres|quattuor|quinque|sex|septem|octo|nouem|novem|decem|undecim|duodecim|tredecim|quattuordecim|quindecim|sedecim|septendecim|uiginti|triginta|quadraginta|quinquaginta|sexaginta|LXV|XXXII|XVIII|XVII|XII|VII|VI|V)\b",
re.I
)

def normalize(text):

    text=text.strip()

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

    words=text.split()

    if len(words)>=2:

        if words[0] in (
            "Vicarii",
            "Duces",
            "Consulares",
            "Correctores",
            "Praesides",
            "Magistri",
            "Comites",
            "Legiones",
            "Auxilia",
            "Pseudocomitatenses",
            "Vexillationes",
            "Procuratores",
            "Praepositi",
            "Rationales",
            "Limitanei",
            "Provinciae",
            "Fabricae"
        ):

            if words[0]=="Magistri":
                return " ".join(words[:2])

            if words[0]=="Comites":
                return " ".join(words[:3])

            if words[0]=="Legiones":
                return " ".join(words[:2])

            if words[0]=="Vexillationes":
                return " ".join(words[:2])

            if words[0]=="Procuratores":
                return " ".join(words[:2])

            if words[0]=="Praepositi":
                return " ".join(words[:2])

            return words[0]

    return text

rows=[]

with open(INPUT,encoding="utf-8") as f:

    reader=csv.DictReader(f)

    for row in reader:

        if row["kind"]!="block":

            continue

        rows.append({

            "nodeId":row["nodeId"],
            "line":row["line"],
            "blockType":normalize(row["text"]),
            "blockText":row["text"]

        })

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
print("Living Notitia")
print("07_normalize_block_types.py")
print()
print("Blocks :",len(rows))
print()
print("Output :",OUTPUT)

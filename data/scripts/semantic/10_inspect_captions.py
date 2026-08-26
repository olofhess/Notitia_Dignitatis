#
# Living Notitia
# 10_inspect_captions.py
#

from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[3]

INPUT=ROOT/"csv"/"BlockType.csv"

captions=[]

STRUCTURE=(
"Sub dispositione",
"Officium",
"Per",
"Intra",
"In provincia",
"In ",
"Item",
"Sub cura",
"Sub iurisdictione",
"Extenditur"
)

HEADINGS=(
"Vicarii",
"Comites rei militaris",
"Duces",
"Consulares",
"Correctores",
"Praesides",
"Magistri scriniorum",
"Legiones",
"Auxilia",
"Pseudocomitatenses",
"Vexillationes",
"Limitanei",
"Fabricae",
"Rationales",
"Procuratores",
"Praepositi"
)

with open(INPUT,encoding="utf-8") as f:

    reader=csv.DictReader(f)

    for row in reader:

        text=row["blockText"]

        skip=False

        for prefix in STRUCTURE:

            if text.startswith(prefix):

                skip=True

                break

        if skip:

            continue

        for prefix in HEADINGS:

            if text.startswith(prefix):

                skip=True

                break

        if skip:

            continue

        captions.append(text)

captions=sorted(set(captions))

print()
print("Living Notitia")
print("10_inspect_captions.py")
print()

print("Captions :",len(captions))
print()

for caption in captions:

    print(caption)
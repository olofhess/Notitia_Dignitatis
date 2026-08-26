#
# Living Notitia
# 09_build_heading_dictionary.py
#

from pathlib import Path
import csv
from collections import Counter

ROOT=Path(__file__).resolve().parents[3]

INPUT=ROOT/"csv"/"BlockType.csv"
OUTPUT=ROOT/"csv"/"HeadingDictionary.csv"

FIELDS=[
"headingType",
"count",
"example"
]

counter=Counter()

examples={}

def classify(text):

    if text.startswith("Sub dispositione"):
        return None

    if text.startswith("Officium"):
        return None

    if text.startswith("Per"):
        return None

    if text.startswith("Intra"):
        return None

    if text.startswith("In provincia"):
        return None

    if text.startswith("In "):
        return None

    if text.startswith("Item"):
        return None

    if text.startswith("Sub cura"):
        return None

    if text.startswith("Sub iurisdictione"):
        return None

    if text.startswith("Extenditur"):
        return None

    if text.startswith("Vicarii"):
        return "officeGroup"

    if text.startswith("Comites rei militaris"):
        return "officeGroup"

    if text.startswith("Duces"):
        return "officeGroup"

    if text.startswith("Consulares"):
        return "officeGroup"

    if text.startswith("Correctores"):
        return "officeGroup"

    if text.startswith("Praesides"):
        return "officeGroup"

    if text.startswith("Magistri scriniorum"):
        return "officeGroup"

    if text.startswith("Legiones"):
        return "unitGroup"

    if text.startswith("Auxilia"):
        return "unitGroup"

    if text.startswith("Pseudocomitatenses"):
        return "unitGroup"

    if text.startswith("Vexillationes"):
        return "unitGroup"

    if text.startswith("Limitanei"):
        return "unitGroup"

    if text.startswith("Fabricae"):
        return "factoryGroup"

    if text.startswith("Rationales"):
        return "financeGroup"

    if text.startswith("Procuratores"):
        return "financeGroup"

    if text.startswith("Praepositi"):
        return "financeGroup"

    return "caption"

with open(INPUT,encoding="utf-8") as f:

    reader=csv.DictReader(f)

    for row in reader:

        headingType=classify(row["blockText"])

        if headingType is None:

            continue

        counter[headingType]+=1

        if headingType not in examples:

            examples[headingType]=row["blockText"]

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

    for headingType,count in sorted(counter.items()):

        writer.writerow({

            "headingType":headingType,
            "count":count,
            "example":examples[headingType]

        })

print()
print("Living Notitia")
print("09_build_heading_dictionary.py")
print()
print("Heading types :",len(counter))
print()
print("Output :",OUTPUT)
#
# Living Notitia
# 08_build_block_dictionary.py
#

from pathlib import Path
import csv
from collections import Counter

ROOT=Path(__file__).resolve().parents[3]

INPUT=ROOT/"csv"/"BlockType.csv"
OUTPUT=ROOT/"csv"/"BlockDictionary.csv"

FIELDS=[
"blockType",
"category",
"semanticType",
"container",
"count",
"example"
]

rows=[]

with open(INPUT,encoding="utf-8") as f:

    reader=csv.DictReader(f)

    for row in reader:

        rows.append(row)

counter=Counter()

examples={}

for row in rows:

    block=row["blockType"]

    counter[block]+=1

    if block not in examples:

        examples[block]=row["blockText"]

def classify(block):

    if block=="Sub dispositione":

        return "structure","office",True

    if block=="Officium":

        return "structure","staff",True

    if block=="Per":

        return "geography","region",True

    if block=="Intra":

        return "geography","region",True

    if block=="In":

        return "geography","region",True

    if block=="In provincia":

        return "geography","province",True

    if block=="Item":

        return "structure","continuation",True

    if block=="Sub cura":

        return "structure","supervision",True

    if block=="Sub iurisdictione":

        return "structure","jurisdiction",True

    if block=="Extenditur":

        return "structure","note",False

    if block=="Vicarii":

        return "administration","officeGroup",True

    if block=="Comites rei militaris":

        return "administration","officeGroup",True

    if block=="Duces":

        return "administration","officeGroup",True

    if block=="Consulares":

        return "administration","officeGroup",True

    if block=="Correctores":

        return "administration","officeGroup",True

    if block=="Praesides":

        return "administration","officeGroup",True

    if block=="Magistri scriniorum":

        return "administration","officeGroup",True

    if block=="Legiones palatinae":

        return "military","unitGroup",True

    if block=="Legiones comitatenses":

        return "military","unitGroup",True

    if block=="Auxilia":

        return "military","unitGroup",True

    if block=="Pseudocomitatenses":

        return "military","unitGroup",True

    if block=="Vexillationes palatinae":

        return "military","unitGroup",True

    if block=="Vexillationes comitatenses":

        return "military","unitGroup",True

    if block=="Limitanei":

        return "military","unitGroup",True

    if block=="Fabricae":

        return "production","factoryGroup",True

    if block=="Rationales":

        return "finance","officeGroup",True

    if block.startswith("Procuratores"):

        return "finance","officeGroup",True

    if block.startswith("Praepositi"):

        return "finance","officeGroup",True

    return "unknown","unknown",False

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

    for block in sorted(counter):

        category,semantic,container=classify(block)

        writer.writerow({

            "blockType":block,
            "category":category,
            "semanticType":semantic,
            "container":"Y" if container else "",
            "count":counter[block],
            "example":examples[block]

        })

print()
print("Living Notitia")
print("08_build_block_dictionary.py")
print()
print("Block types :",len(counter))
print()
print("Output :",OUTPUT)
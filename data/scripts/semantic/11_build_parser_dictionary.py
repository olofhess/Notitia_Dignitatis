#
# Living Notitia
# 11_build_parser_dictionary.py
#

from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[3]

INPUT=ROOT/"csv"/"BlockType.csv"
OUTPUT=ROOT/"csv"/"ParserDictionary.csv"

FIELDS=[
"pattern",
"nodeType",
"class",
"container",
"priority"
]

rows=[]

def add(pattern,nodeType,nodeClass,container,priority):

    rows.append({

        "pattern":pattern,
        "nodeType":nodeType,
        "class":nodeClass,
        "container":container,
        "priority":priority

    })

#
# Structural blocks
#

add("Sub dispositione","block","structure","Y",10)
add("Officium","block","structure","Y",10)
add("Per ","block","structure","Y",20)
add("Intra ","block","structure","Y",20)
add("In provincia","block","structure","Y",20)
add("In ","block","structure","Y",30)
add("Item","block","structure","Y",30)
add("Sub cura","block","structure","Y",20)
add("Sub iurisdictione","block","structure","Y",20)
add("Extenditur","block","note","",90)

#
# Administrative headings
#

add("Vicarii","heading","officeGroup","Y",40)
add("Comites rei militaris","heading","officeGroup","Y",40)
add("Duces","heading","officeGroup","Y",40)
add("Consulares","heading","officeGroup","Y",40)
add("Correctores","heading","officeGroup","Y",40)
add("Praesides","heading","officeGroup","Y",40)
add("Magistri scriniorum","heading","officeGroup","Y",40)

#
# Military headings
#

add("Legiones palatinae","heading","unitGroup","Y",50)
add("Legiones comitatenses","heading","unitGroup","Y",50)
add("Auxilia","heading","unitGroup","Y",50)
add("Pseudocomitatenses","heading","unitGroup","Y",50)
add("Vexillationes palatinae","heading","unitGroup","Y",50)
add("Vexillationes comitatenses","heading","unitGroup","Y",50)
add("Limitanei","heading","unitGroup","Y",50)
add("Comites limitum","heading","unitGroup","Y",50)
add("duces limitum","heading","unitGroup","Y",50)

#
# Production
#

add("Fabricae","heading","factoryGroup","Y",60)

#
# Finance
#

add("Rationales","heading","financeGroup","Y",70)
add("Praepositi","heading","financeGroup","Y",70)
add("Procuratores","heading","financeGroup","Y",70)

#
# Geographic headings
#

add("Provinciae","heading","geographicGroup","Y",80)
add("Italiae","heading","geographicGroup","Y",80)
add("Illyrici","heading","geographicGroup","Y",80)
add("Africae","heading","geographicGroup","Y",80)
add("Britanniarum","heading","geographicGroup","Y",80)
add("Hispaniarum","heading","geographicGroup","Y",80)
add("Septem provinciarum","heading","geographicGroup","Y",80)
add("Hispaniae","heading","geographicGroup","Y",80)
add("Orientalium","heading","geographicGroup","Y",80)
add("Gallicanarum","heading","geographicGroup","Y",80)

#
# Misc
#

add("peditum","heading","misc","",90)

rows.sort(key=lambda r:(int(r["priority"]),r["pattern"]))

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
print("11_build_parser_dictionary.py")
print()
print("Patterns :",len(rows))
print()
print("Output :",OUTPUT)
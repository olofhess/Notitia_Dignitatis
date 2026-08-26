#
# Living Notitia
# build_navigator.py
#

from pathlib import Path
import csv
import re

ROOT=Path(__file__).resolve().parents[1]

INPUT=ROOT/"data"/"Notitia_OCC.txt"
OUTPUT=ROOT/"csv"/"Navigator.csv"

FIELDS=[
"nodeId",
"parentId",
"level",
"label"
]

ROMAN=re.compile(r"^([IVXLCDM]+)\.\s+(.*)$")

TOP_LEVEL=(
"Praefectus ",
"Magister ",
"Praepositus ",
"Quaestor",
"Comes ",
"Primicerius ",
"Castrensis ",
"Proconsul ",
"Magistri scriniorum",
"Vicarii ",
"Comites rei militaris",
"Duces ",
"Consulares ",
"Correctores ",
"Praesides "
)

rows=[]
stack={}
nextId=1
insideIndex=False

def newId():

    global nextId

    nodeId=f"N{nextId:05d}"

    nextId+=1

    return nodeId

def addNode(parentId,level,label):

    nodeId=newId()

    rows.append({

        "nodeId":nodeId,
        "parentId":parentId,
        "level":level,
        "label":label

    })

    stack[level]=nodeId

    for key in list(stack.keys()):

        if key>level:

            del stack[key]

    return nodeId

def indentation(line):

    return len(line)-len(line.lstrip(" "))

def isTopLevel(label):

    for prefix in TOP_LEVEL:

        if label.startswith(prefix):

            return True

    return False

with open(INPUT,encoding="utf-8") as f:

    lines=[line.rstrip("\n") for line in f]

documentId=addNode(
    "",
    0,
    "Occidentis"
)

chapterId=None
currentGroup=None
currentRegion=None

for raw in lines:

    text=raw.strip()

    if not text:

        continue

    m=ROMAN.match(text)

    if m:

        if m.group(1)=="I":

            insideIndex=True

            chapterId=addNode(
                documentId,
                1,
                text
            )

            continue

        if insideIndex:

            break

    if not insideIndex:

        continue

    label=text.rstrip(".").rstrip(":")

    if isTopLevel(label):

        currentGroup=addNode(
            chapterId,
            2,
            label
        )

        currentRegion=None

        continue

    if label.startswith("Per "):

        currentRegion=addNode(
            currentGroup,
            3,
            label
        )

        continue

    indent=indentation(raw)

    if currentRegion:

        parent=currentRegion
        level=4

    elif currentGroup:

        parent=currentGroup
        level=3

    else:

        parent=chapterId
        level=2

    addNode(
        parent,
        level,
        label
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
print("Living Notitia")
print("build_navigator.py")
print()
print("Rows :",len(rows))
print()
print("Output:",OUTPUT)
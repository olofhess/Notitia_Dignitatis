#
# Living Notitia
# 12_parse_structure_v2.py
#

from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[3]

TEXT=ROOT/"data"/"Notitia_OCC.txt"
CHAPTERS=ROOT/"csv"/"ChapterIndex.csv"
RULES=ROOT/"csv"/"ParserDictionary.csv"
OUTPUT=ROOT/"csv"/"Structure.csv"

FIELDS=[
"nodeId",
"parentId",
"level",
"kind",
"line",
"text"
]

chapters=[]
rules=[]
rows=[]

with open(CHAPTERS,encoding="utf-8") as f:

    reader=csv.DictReader(f)

    for row in reader:

        row["lineStart"]=int(row["lineStart"])
        row["lineEnd"]=int(row["lineEnd"])

        chapters.append(row)

with open(RULES,encoding="utf-8") as f:

    reader=csv.DictReader(f)

    for row in reader:

        row["priority"]=int(row["priority"])

        rules.append(row)

rules.sort(key=lambda r:r["priority"])

with open(TEXT,encoding="utf-8") as f:

    lines=[line.rstrip("\n") for line in f]

nextId=1

def newId():

    global nextId

    nodeId=f"S{nextId:05d}"

    nextId+=1

    return nodeId

documentId=newId()

rows.append({

    "nodeId":documentId,
    "parentId":"",
    "level":0,
    "kind":"document",
    "line":"",
    "text":"Occidentis"

})

currentChapter=None
currentBlock=None

for chapter in chapters:

    chapterId=newId()

    rows.append({

        "nodeId":chapterId,
        "parentId":documentId,
        "level":1,
        "kind":"chapter",
        "line":chapter["lineStart"],
        "text":chapter["chapter"]

    })

    titleId=newId()

    rows.append({

        "nodeId":titleId,
        "parentId":chapterId,
        "level":2,
        "kind":"title",
        "line":chapter["lineStart"],
        "text":chapter["title"]

    })

    currentChapter=chapterId
    currentBlock=None

    for lineNumber in range(

        chapter["lineStart"]+1,
        chapter["lineEnd"]+1

    ):

        text=lines[lineNumber-1].strip()

        if not text:

            continue

        matched=None

        for rule in rules:

            if text.startswith(rule["pattern"]):

                matched=rule

                break

        if matched:

            nodeId=newId()

            rows.append({

                "nodeId":nodeId,
                "parentId":currentChapter,
                "level":2,
                "kind":matched["nodeType"],
                "line":lineNumber,
                "text":text

            })

            if matched["container"]=="Y":

                currentBlock=nodeId

        else:

            if currentBlock:

                parent=currentBlock
                level=3

            else:

                parent=currentChapter
                level=2

            rows.append({

                "nodeId":newId(),
                "parentId":parent,
                "level":level,
                "kind":"entry",
                "line":lineNumber,
                "text":text

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
print("12_parse_structure_v2.py")
print()
print("Rows :",len(rows))
print("Output :",OUTPUT)
#
# Living Notitia
# 04_parse_structure.py
#
from pathlib import Path
import csv
import re
ROOT=Path(__file__).resolve().parents[3]
INPUT=ROOT/"data"/"Notitia_OCC.txt"
OUTPUT=ROOT/"csv"/"Structure.csv"
FIELDS=[
"nodeId",
"parentId",
"level",
"kind",
"line",
"text"
]
CHAPTER=re.compile(r"^([IVXLCDM]+)[\.:]\s*(.*)$")
rows=[]
nextId=1
currentChapter=None
blockStack=[]
def newId():
    global nextId
    nodeId=f"S{nextId:05d}"
    nextId+=1
    return nodeId
def indentation(line):
    return len(line)-len(line.lstrip(" "))
def addNode(parentId,level,kind,lineNumber,text):
    nodeId=newId()
    rows.append({
        "nodeId":nodeId,
        "parentId":parentId,
        "level":level,
        "kind":kind,
        "line":lineNumber,
        "text":text
    })
    return nodeId
def currentParent():
    if blockStack:
        return blockStack[-1]["nodeId"],blockStack[-1]["level"]+1
    if currentChapter:
        return currentChapter,1
    return "",0
def closeForBlock(indent):
    while blockStack and indent<=blockStack[-1]["indent"]:
        blockStack.pop()
def closeForEntry(indent):
    while blockStack:
        top=blockStack[-1]
        if indent<top["indent"]:
            blockStack.pop()
            continue
        if indent==top["indent"] and top["seenDeeper"]:
            blockStack.pop()
            continue
        break
def markDeeper(indent):
    for block in blockStack:
        if indent>block["indent"]:
            block["seenDeeper"]=True
with open(INPUT,encoding="utf-8") as f:
    lines=[line.rstrip("\n") for line in f]
documentId=addNode(
    "",
    0,
    "document",
    1,
    "Occidentis"
)
for lineNumber,raw in enumerate(lines,start=1):
    text=raw.strip()
    if not text:
        continue
    match=CHAPTER.match(text)
    if match:
        roman=match.group(1)
        title=match.group(2).strip()
        blockStack=[]
        currentChapter=addNode(
            documentId,
            1,
            "chapter",
            lineNumber,
            roman
        )
        if title:
            addNode(
                currentChapter,
                2,
                "title",
                lineNumber,
                title
            )
        continue
    if currentChapter is None:
        continue
    indent=indentation(raw)
    if text.endswith(":"):
        closeForBlock(indent)
        markDeeper(indent)
        parentId,level=currentParent()
        label=text[:-1].strip()
        nodeId=addNode(
            parentId,
            level,
            "block",
            lineNumber,
            label
        )
        blockStack.append({
            "nodeId":nodeId,
            "indent":indent,
            "level":level,
            "seenDeeper":False
        })
        continue
    closeForEntry(indent)
    markDeeper(indent)
    parentId,level=currentParent()
    addNode(
        parentId,
        level,
        "entry",
        lineNumber,
        text.rstrip(".")
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
print("04_parse_structure.py")
print()
print("Rows     :",len(rows))
print("Chapters :",sum(1 for row in rows if row["kind"]=="chapter"))
print("Blocks   :",sum(1 for row in rows if row["kind"]=="block"))
print("Entries  :",sum(1 for row in rows if row["kind"]=="entry"))
print()
print("Output:",OUTPUT)
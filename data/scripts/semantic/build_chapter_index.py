#
# Living Notitia
# build_chapter_index.py
#
from pathlib import Path
import csv
import re
ROOT=Path(__file__).resolve().parents[3]
INPUT=ROOT/"data"/"Notitia.txt"
OUTPUT=ROOT/"csv"/"ChapterIndex.csv"
FIELDS=[
    "document",
    "chapter",
    "title",
    "lineStart",
    "lineEnd"
]
ROMAN=re.compile(r"^([IVXLCDM]+)\.\s+(.*)$")
DOCUMENT=re.compile(r"^DOCUMENT:\s*(.+)$")
with open(INPUT,encoding="utf-8") as f:
    lines=[line.rstrip("\n") for line in f]
chapters=[]
currentDocument=None
for lineNumber,line in enumerate(lines,start=1):
    text=line.strip()
    if not text:
        continue
    d=DOCUMENT.match(text)
    if d:
        currentDocument=d.group(1).strip()
        continue
    m=ROMAN.match(text)
    if not m:
        continue
    roman=m.group(1)
    title=m.group(2).rstrip(".")
    chapters.append({
        "document":currentDocument,
        "chapter":roman,
        "title":title,
        "lineStart":lineNumber
    })
for i,row in enumerate(chapters):
    document=row["document"]
    nextChapter=None
    for j in range(i+1,len(chapters)):
        if chapters[j]["document"]==document:
            nextChapter=chapters[j]
            break
        if chapters[j]["document"]!=document:
            break
    if nextChapter:
        row["lineEnd"]=nextChapter["lineStart"]-1
    else:
        lineEnd=len(lines)
        for lineNumber in range(row["lineStart"],len(lines)+1):
            text=lines[lineNumber-1].strip()
            d=DOCUMENT.match(text)
            if d and lineNumber>row["lineStart"]:
                lineEnd=lineNumber-1
                break
        row["lineEnd"]=lineEnd
with open(OUTPUT,"w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(chapters)
print()
print("Living Notitia")
print("build_chapter_index.py")
print()
documents={}
for row in chapters:
    document=row["document"]
    documents[document]=documents.get(document,0)+1
for document,count in documents.items():
    print(document,":",count,"chapters")
print()
print("Chapters :",len(chapters))
print()
print("Output :",OUTPUT)
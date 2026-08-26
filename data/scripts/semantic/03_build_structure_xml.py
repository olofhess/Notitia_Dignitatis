#
# Living Notitia
# build_structure_xml.py
#
from pathlib import Path
import csv
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
CHAPTERS=ROOT/"csv"/"ChapterIndex.csv"
TEXT=ROOT/"data"/"Notitia.txt"
OUTPUT=ROOT/"data"/"Notitia.xml"
chapters=[]
with open(CHAPTERS,encoding="utf-8") as f:
    reader=csv.DictReader(f)
    for row in reader:
        row["lineStart"]=int(row["lineStart"])
        row["lineEnd"]=int(row["lineEnd"])
        chapters.append(row)
with open(TEXT,encoding="utf-8") as f:
    lines=[line.rstrip("\n") for line in f]
def indentation(text):
    return len(text)-len(text.lstrip(" "))
root=ET.Element("notitia")
documents={}
for row in chapters:
    documentName=row["document"]
    if documentName not in documents:
        document=ET.SubElement(
            root,
            "document"
        )
        document.set(
            "id",
            documentName
        )
        documents[documentName]=document
    document=documents[documentName]
    chapter=ET.SubElement(
        document,
        "chapter"
    )
    chapter.set(
        "number",
        row["chapter"]
    )
    title=ET.SubElement(
        chapter,
        "title"
    )
    title.text=row["title"]
    blockStack=[]
    for lineNumber in range(
        row["lineStart"]+1,
        row["lineEnd"]+1
    ):
        text=lines[lineNumber-1].rstrip()
        if not text:
            continue
        if text.startswith("DOCUMENT:"):
            continue
        indent=indentation(text)
        label=text.strip()
        while blockStack and indent<=blockStack[-1][0]:
            blockStack.pop()
        parent=chapter
        if blockStack:
            parent=blockStack[-1][1]
        if label.endswith(":"):
            block=ET.SubElement(
                parent,
                "block"
            )
            title=ET.SubElement(
                block,
                "title"
            )
            title.text=label[:-1]
            blockStack.append(
                (
                    indent,
                    block
                )
            )
        else:
            entry=ET.SubElement(
                parent,
                "entry"
            )
            entry.set(
                "line",
                str(lineNumber)
            )
            entry.text=label.rstrip(".")
tree=ET.ElementTree(root)
ET.indent(
    tree,
    space="    "
)
tree.write(
    OUTPUT,
    encoding="utf-8",
    xml_declaration=True
)
print()
print("Living Notitia")
print("build_structure_xml.py")
print()
print("Documents :",len(documents))
for documentName in documents:
    count=sum(
        1
        for row in chapters
        if row["document"]==documentName
    )
    print(documentName,":",count,"chapters")
print()
print("Chapters  :",len(chapters))
print("Lines     :",len(lines))
print()
print("Output :",OUTPUT)
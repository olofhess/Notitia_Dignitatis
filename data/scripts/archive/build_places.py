#
# Living Notitia V3
# build_places.py
#
from pathlib import Path
import csv
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
INPUT=ROOT/"data"/"notitia.xml"
OUTPUT=ROOT/"csv"/"Place.csv"
FIELDS=[
"placeId",
"placeName",
"nodeType",
"office",
"unit",
"chapter",
"document"
]
tree=ET.parse(INPUT)
root=tree.getroot()
rows=[]
seen=set()
placeNumber=1
for document in root.findall("document"):
    documentName=document.get("id","")
    for chapter in document.findall("chapter"):
        chapterTitle=""
        title=chapter.find("title")
        if title is not None and title.text:
            chapterTitle=title.text.strip()
        for node in chapter.iter():
            placeNode=node.find("place")
            if placeNode is None:
                continue
            placeName=(placeNode.text or "").strip()
            if not placeName:
                continue
            nodeType=node.tag
            office=""
            officeNode=node.find("office")
            if officeNode is not None and officeNode.text:
                office=officeNode.text.strip()
            unit=""
            unitNode=node.find("unit")
            if unitNode is not None and unitNode.text:
                unit=unitNode.text.strip()
            key=(
                placeName,
                nodeType,
                office,
                unit,
                chapterTitle,
                documentName
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "placeId":f"PLC{placeNumber:05d}",
                "placeName":placeName,
                "nodeType":nodeType,
                "office":office,
                "unit":unit,
                "chapter":chapterTitle,
                "document":documentName
            })
            placeNumber+=1
rows.sort(
    key=lambda r:(
        r["placeName"].lower(),
        r["chapter"],
        r["nodeType"],
        r["unit"]
    )
)
with open(OUTPUT,"w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
print()
print("Living Notitia V3")
print("build_places.py")
print()
print("Places :",len(rows))
print()
print("Output :",OUTPUT)
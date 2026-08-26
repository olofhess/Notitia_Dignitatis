#
# Living Notitia
# build_geography.py
#

from pathlib import Path
import csv
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

INPUT=ROOT/"data"/"notitia.xml"
OUTPUT=ROOT/"csv"/"Geography.csv"

FIELDS=[
"geoId",
"parentGeoId",
"geoType",
"name",
"chapter",
"line"
]

rows=[]
nextId=1


def make_geo_id():

    global nextId

    geoId=f"G{nextId:06d}"

    nextId+=1

    return geoId


def clean(text):

    if text is None:
        return ""

    text=text.strip()

    text=text.rstrip(".")

    text=re.sub(r"\s+"," ",text)

    return text


def title(node):

    t=node.find("title")

    if t is not None and t.text:

        return clean(t.text)

    if node.text:

        return clean(node.text)

    return ""


def line(node):

    return node.attrib.get("line","")


def add_row(parentId,geoType,name,chapter,lineNo):

    rows.append({
        "geoId":make_geo_id(),
        "parentGeoId":parentId,
        "geoType":geoType,
        "name":name,
        "chapter":chapter,
        "line":lineNo
    })

    return rows[-1]["geoId"]


tree=ET.parse(INPUT)

root=tree.getroot()

def build():

    for document in root.findall("document"):

        for chapter in document.findall("chapter"):

            chapterTitle=title(chapter)

            for group in chapter.findall("group"):

                if title(group)!="Provinciae":
                    continue

                for area in group.findall("group"):

                    areaTitle=title(area)

                    areaName=re.sub(r"\s+[IVXLCDM0-9]+$","",areaTitle)
                    areaName=re.sub(
                        r"\s+(unus|unum|una|duo|duae|tres|quattuor|quinque|sex|septem|octo|novem|decem|undecim|duodecim|tredecim|quattuordecim|quindecim|sedecim|septendecim|duodeviginti)$",
                        "",
                        areaName,
                        flags=re.IGNORECASE
                    )

                    areaName=clean(areaName)

                    parentId=add_row(
                        "",
                        "area",
                        areaName,
                        chapterTitle,
                        line(area)
                    )

                    for item in area.findall("item"):

                        province=clean(title(item))

                        if province=="":

                            continue

                        add_row(
                            parentId,
                            "province",
                            province,
                            chapterTitle,
                            line(item)
                        )
build()

with open(OUTPUT,"w",newline="",encoding="utf-8") as f:

    writer=csv.DictWriter(
        f,
        fieldnames=FIELDS,
        delimiter=";"
    )

    writer.writeheader()

    writer.writerows(rows)

areas=sum(
    1
    for row in rows
    if row["geoType"]=="area"
)

provinces=sum(
    1
    for row in rows
    if row["geoType"]=="province"
)

print()

print("Living Notitia")
print("build_geography.py")
print()

print(f"Areas      : {areas}")
print(f"Provinces  : {provinces}")
print(f"Rows       : {len(rows)}")
print()

print(f"Output: {OUTPUT}")                        
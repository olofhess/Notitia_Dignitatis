#
# Living Notitia
# inspect_province_matches.py
#
from pathlib import Path
import csv
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]

XML_FILE=ROOT/"data"/"Notitia.xml"
MATCH_FILE=ROOT/"csv"/"ProvinceMatch.csv"
OUTPUT=ROOT/"csv"/"ProvinceMatchReport.csv"

CATEGORY_PATTERNS=[
    ("dux",re.compile(r"^Duces\b",re.I)),
    ("consularis",re.compile(r"^Consulares\b",re.I)),
    ("corrector",re.compile(r"^Correctores\b",re.I)),
    ("praeses",re.compile(r"^Praesides\b",re.I))
]

FIELDS=[
    "document",
    "sourceClass",
    "sourceGroup",
    "notitiaName",
    "sourceLine",
    "gisProvince",
    "canonicalName",
    "matchStatus"
]

def clean(text):
    if text is None:
        return ""
    return " ".join(
        text.strip()
            .rstrip(".:")
            .split()
    )

def block_title(block):
    node=block.find("title")
    if node is None:
        return ""
    return clean(node.text)

def classify_category(title):
    for name,pattern in CATEGORY_PATTERNS:
        if pattern.search(title):
            return name
    return None

tree=ET.parse(XML_FILE)
root=tree.getroot()

references=[]

for document in root.findall("document"):

    documentName=document.get("id","")

    chapter=document.find(
        "chapter[@number='I']"
    )

    if chapter is None:
        continue

    for block in chapter.findall("block"):

        categoryTitle=block_title(block)
        sourceClass=classify_category(
            categoryTitle
        )

        if not sourceClass:
            continue

        for child in list(block):

            if child.tag=="title":
                continue

            if child.tag=="entry":

                name=clean(child.text)

                if not name:
                    continue

                references.append({
                    "document":documentName,
                    "sourceClass":sourceClass,
                    "sourceGroup":"",
                    "notitiaName":name,
                    "sourceLine":child.get(
                        "line",
                        ""
                    )
                })

            elif child.tag=="block":

                groupTitle=block_title(child)

                for entry in child.findall(
                    ".//entry"
                ):

                    name=clean(entry.text)

                    if not name:
                        continue

                    references.append({
                        "document":documentName,
                        "sourceClass":sourceClass,
                        "sourceGroup":groupTitle,
                        "notitiaName":name,
                        "sourceLine":entry.get(
                            "line",
                            ""
                        )
                    })

matchRows=[]

with open(
    MATCH_FILE,
    encoding="utf-8-sig"
) as f:

    reader=csv.DictReader(f)

    for row in reader:
        matchRows.append(row)

matchIndex={}

for row in matchRows:

    notitiaName=clean(
        row.get(
            "notitiaMatch",
            ""
        )
    )

    if not notitiaName:
        continue

    matchIndex[
        notitiaName.casefold()
    ]=row

report=[]

matched=0
unmatched=0

seen=set()

for reference in references:

    name=reference["notitiaName"]
    key=name.casefold()

    if key in seen:
        continue

    seen.add(key)

    match=matchIndex.get(key)

    if match:

        status="MATCH"
        matched+=1

        gisProvince=clean(
            match.get(
                "gisProvince",
                ""
            )
        )

        canonicalName=clean(
            match.get(
                "canonicalName",
                ""
            )
        )

    else:

        status="UNMATCHED"
        unmatched+=1
        gisProvince=""
        canonicalName=""

    report.append({
        "document":reference["document"],
        "sourceClass":reference["sourceClass"],
        "sourceGroup":reference["sourceGroup"],
        "notitiaName":name,
        "sourceLine":reference["sourceLine"],
        "gisProvince":gisProvince,
        "canonicalName":canonicalName,
        "matchStatus":status
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
    writer.writerows(report)

print()
print("Living Notitia")
print("inspect_province_matches.py")
print()

print(
    "Province references :",
    len(references)
)

print(
    "Unique names        :",
    len(report)
)

print(
    "ProvinceMatch rows  :",
    len(matchRows)
)

print(
    "Matched             :",
    matched
)

print(
    "Unmatched           :",
    unmatched
)

print()
print("BY DOCUMENT")
print("--------------------------------")

for documentName in (
    "Occidentis",
    "Oriens"
):

    count=sum(
        1
        for row in report
        if row["document"]==documentName
    )

    print(
        documentName,
        ":",
        count
    )

print()
print("UNMATCHED")
print("--------------------------------")

for row in report:

    if row["matchStatus"]!="UNMATCHED":
        continue

    print(
        row["document"],
        "|",
        row["sourceClass"],
        "|",
        row["sourceGroup"],
        "|",
        row["notitiaName"]
    )

print()
print("Output :",OUTPUT)
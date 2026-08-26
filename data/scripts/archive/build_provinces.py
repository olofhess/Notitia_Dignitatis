#
# Living Notitia
# build_provinces.py
#

from pathlib import Path
import csv
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

INPUT=ROOT/"data"/"notitia.xml"
OUTPUT=ROOT/"data"/"Province.csv"

FIELDS=[
    "provinceId",
    "provinceName",
    "chapter"
]

rows=[]
seen=set()
group_titles=set()
province_number=1


def add_province(name,chapter):
    global province_number

    if name is None:
        return

    name=name.strip().rstrip(".")

    if not name:
        return

    if name in seen:
        return

    seen.add(name)

    rows.append({
        "provinceId":f"PRO{province_number:05d}",
        "provinceName":name,
        "chapter":chapter
    })

    province_number+=1


def is_province_group(title):

    return (
        title.startswith("Consulares")
        or title.startswith("Correctores")
        or title.startswith("Praesides")
        or title.startswith("Proconsules")
    )


tree=ET.parse(INPUT)
root=tree.getroot()

for document in root.findall("document"):

    for chapter in document.findall("chapter"):

        chapter_title=chapter.findtext("title","").strip()

        for group in chapter.iter("group"):

            title=group.findtext("title","").strip()

            if title:
                group_titles.add(title)

            if not is_province_group(title):
                continue

            subgroups=group.findall("group")

            #
            # Province lists divided into subgroups
            #

            if subgroups:

                for subgroup in subgroups:

                    for item in subgroup.findall("item"):

                        if item.find("unit") is not None:
                            continue

                        add_province(item.text,chapter_title)

            #
            # Ordinary province list
            #

            else:

                for item in group.findall("item"):

                    if item.find("unit") is not None:
                        continue

                    add_province(item.text,chapter_title)


with open(OUTPUT,"w",newline="",encoding="utf-8") as f:

    writer=csv.DictWriter(f,fieldnames=FIELDS)

    writer.writeheader()
    writer.writerows(rows)


print()
print("Living Notitia")
print("build_provinces.py")
print()

print("Group titles")
print("--------------------------------")

for title in sorted(group_titles):
    print(title)

print()
print("Provinces :",len(rows))
print()
print("Output :",OUTPUT)
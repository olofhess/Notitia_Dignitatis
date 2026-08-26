#
# Living Notitia
# 13_validate_structure.py
#

from pathlib import Path
import csv
from collections import Counter

ROOT=Path(__file__).resolve().parents[3]

INPUT=ROOT/"csv"/"Structure.csv"

rows=[]
index={}
children=Counter()

with open(INPUT,encoding="utf-8") as f:

    reader=csv.DictReader(f)

    for row in reader:

        row["level"]=int(row["level"])

        rows.append(row)

        index[row["nodeId"]]=row

for row in rows:

    if row["parentId"]:

        children[row["parentId"]]+=1

errors=0
warnings=0

print()
print("Living Notitia")
print("13_validate_structure.py")
print()

for row in rows:

    node=row["nodeId"]
    parent=row["parentId"]
    level=row["level"]
    kind=row["kind"]

    if parent and parent not in index:

        print("ERROR Missing parent :",node)

        errors+=1

        continue

    if parent:

        parentRow=index[parent]

        if level!=parentRow["level"]+1:

            print("ERROR Level :",node)

            errors+=1

        if parent==node:

            print("ERROR Self parent :",node)

            errors+=1

    if kind=="chapter":

        titleCount=0

        for r in rows:

            if r["parentId"]==node and r["kind"]=="title":

                titleCount+=1

        if titleCount!=1:

            print("ERROR Chapter title :",node)

            errors+=1

    if kind=="block":

        if children[node]==0:

            print("WARNING Empty block :",node)

            warnings+=1

    if kind=="heading":

        if children[node]==0:

            print("WARNING Empty heading :",node)

            warnings+=1

visited=set()

def walk(node):

    global errors

    if node in visited:

        print("ERROR Cycle :",node)

        errors+=1

        return

    visited.add(node)

    for row in rows:

        if row["parentId"]==node:

            walk(row["nodeId"])

walk(rows[0]["nodeId"])

for row in rows:

    if row["nodeId"] not in visited:

        print("ERROR Orphan :",row["nodeId"])

        errors+=1

print()
print("Rows      :",len(rows))
print("Visited   :",len(visited))
print("Errors    :",errors)
print("Warnings  :",warnings)
print()
print("Node types")
print("--------------------------------")

counter=Counter()

for row in rows:

    counter[row["kind"]]+=1

for kind,count in sorted(counter.items()):

    print(f"{kind:12} {count:5}")
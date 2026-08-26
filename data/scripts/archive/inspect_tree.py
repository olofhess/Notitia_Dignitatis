#
# Living Notitia
# inspect_tree.py
#

from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

INPUT=ROOT/"data"/"notitia.xml"
OUTPUT=ROOT/"data"/"TreeReport.txt"


def title(node):

    t=node.find("title")

    if t is not None and t.text:
        return t.text.strip()

    if node.text:
        return node.text.strip()

    return ""


def write_node(f,node,level):

    indent="    "*level

    text=title(node)

    line=node.attrib.get("line","")

    if line:
        f.write(f"{indent}{node.tag} [{line}] {text}\n")
    else:
        f.write(f"{indent}{node.tag} {text}\n")

    for child in node:

        if child.tag=="title":
            continue

        write_node(f,child,level+1)


tree=ET.parse(INPUT)
root=tree.getroot()

with open(OUTPUT,"w",encoding="utf-8") as f:

    f.write("Living Notitia\n")
    f.write("XML Tree Report\n")
    f.write("="*60+"\n\n")

    for document in root.findall("document"):

        write_node(f,document,0)

        f.write("\n")

print()
print("Living Notitia")
print("inspect_tree.py")
print()
print("Output :",OUTPUT)
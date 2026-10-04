from pathlib import Path
import csv
import xml.etree.ElementTree as ET

XML_FILE = Path("data/notitia.xml")
OUT_FILE = Path("csv/BodleianChapterMap.csv")

tree = ET.parse(XML_FILE)
root = tree.getroot()

rows = []

for document in root.findall("document"):
    document_id = document.get("id", "")

    chapters = document.findall("chapter")

    for number, chapter in enumerate(chapters, start=1):
        title_node = chapter.find("title")
        title = (
            "".join(title_node.itertext()).strip()
            if title_node is not None
            else ""
        )

        rows.append({
            "document": document_id,
            "chapter": number,
            "title": title,
            "start_folio": "",
            "url": "",
            "status": "unmatched",
        })

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with OUT_FILE.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "document",
            "chapter",
            "title",
            "start_folio",
            "url",
            "status",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} chapters to {OUT_FILE}")
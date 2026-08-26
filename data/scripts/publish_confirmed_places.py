#!/usr/bin/env python3
from pathlib import Path
import csv
import shutil
from datetime import datetime
HERE=Path(__file__).resolve()
def find_root():
    for parent in [HERE.parent,*HERE.parents]:
        if (parent/"csv"/"PlaceMatch_context.csv").exists():
            return parent
    raise FileNotFoundError("Hittar inte projektroten med csv/PlaceMatch_context.csv")
ROOT=find_root()
MATCH_INPUT=ROOT/"csv"/"PlaceMatch_context.csv"
CONFIRMED_OUTPUT=ROOT/"csv"/"PlaceConfirmed.csv"
SOURCE_CANDIDATES=[
    ROOT/"data"/"core"/"SourceNode.csv",
    ROOT/"data"/"work"/"SourceNode.csv",
    ROOT/"data"/"SourceNode.csv",
    ROOT/"web"/"data"/"core"/"SourceNode.csv",
    ROOT/"web"/"data"/"work"/"SourceNode.csv",
    ROOT/"web"/"data"/"SourceNode.csv"
]
APP_OUTPUTS=[ROOT/"data"/"work"/"Places.csv"]
if (ROOT/"web").exists():
    APP_OUTPUTS.append(ROOT/"web"/"data"/"work"/"Places.csv")
FIELDS=[
    "placeId",
    "sourceNodeId",
    "occurrenceId",
    "placeName",
    "pleiadesId",
    "pleiadesName",
    "latitude",
    "longitude",
    "featureType",
    "document",
    "chapter",
    "office",
    "unit",
    "sourceLine",
    "matchType",
    "confidence",
    "contextStatus",
    "gisProvince",
    "expectedProvince",
    "hardProvince",
    "softProvince",
    "region"
]
def clean(value):
    return str(value or "").strip()
def docnorm(value):
    value=clean(value).lower().replace("_"," ").replace("-"," ")
    if "occident" in value or value=="occidens":
        return "occidentis"
    if "orient" in value or value=="oriens":
        return "orientis"
    return " ".join(value.split())
def detect_delimiter(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        sample=f.read(4096)
    try:
        return csv.Sniffer().sniff(sample,delimiters=",;\t").delimiter
    except csv.Error:
        first=sample.splitlines()[0] if sample.splitlines() else ""
        return ";" if first.count(";")>first.count(",") else ","
def read_csv(path):
    delimiter=detect_delimiter(path)
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f,delimiter=delimiter))
def source_index():
    source=next((path for path in SOURCE_CANDIDATES if path.exists()),None)
    if source is None:
        return None,{}
    rows=read_csv(source)
    index={}
    for row in rows:
        line=clean(row.get("sourceLine"))
        document=docnorm(row.get("document"))
        node_id=clean(row.get("nodeId") or row.get("sourceNodeId"))
        if not line or not node_id:
            continue
        key=(document,line)
        current=index.get(key)
        node_type=clean(row.get("nodeType")).lower()
        if current is None or node_type in {"item","entry","unknown"}:
            index[key]=node_id
    return source,index
def valid_number(value):
    try:
        float(clean(value))
        return True
    except ValueError:
        return False
def backup(path):
    if not path.exists():
        return None
    stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
    archive=path.parent/"archive"
    archive.mkdir(parents=True,exist_ok=True)
    target=archive/f"{path.stem}_{stamp}{path.suffix}"
    shutil.copy2(path,target)
    return target
def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
matches=read_csv(MATCH_INPUT)
source_file,source_by_line=source_index()
rows=[]
seen=set()
without_coordinates=[]
for match in matches:
    occurrence_id=clean(match.get("occurrenceId"))
    if occurrence_id in seen:
        continue
    seen.add(occurrence_id)
    latitude=clean(match.get("latitude"))
    longitude=clean(match.get("longitude"))
    if not valid_number(latitude) or not valid_number(longitude):
        without_coordinates.append(occurrence_id)
        continue
    document=clean(match.get("document"))
    source_line=clean(match.get("sourceLine"))
    source_node_id=source_by_line.get((docnorm(document),source_line),"")
    rows.append({
        "placeId":occurrence_id or f"PLACE{len(rows)+1:06d}",
        "sourceNodeId":source_node_id,
        "occurrenceId":occurrence_id,
        "placeName":clean(match.get("placeName")),
        "pleiadesId":clean(match.get("pleiadesId")),
        "pleiadesName":clean(match.get("pleiadesName")),
        "latitude":latitude,
        "longitude":longitude,
        "featureType":clean(match.get("featureType")),
        "document":document,
        "chapter":clean(match.get("chapter")),
        "office":clean(match.get("office")),
        "unit":clean(match.get("unit")),
        "sourceLine":source_line,
        "matchType":clean(match.get("matchType")),
        "confidence":"confirmed",
        "contextStatus":clean(match.get("contextStatus")),
        "gisProvince":clean(match.get("gisProvince")),
        "expectedProvince":clean(match.get("expectedProvince")),
        "hardProvince":clean(match.get("hardProvince")),
        "softProvince":clean(match.get("softProvince")),
        "region":clean(match.get("region"))
    })
rows.sort(key=lambda r:(r["document"],int(r["sourceLine"]) if r["sourceLine"].isdigit() else 999999,r["occurrenceId"]))
backups=[]
for output in [CONFIRMED_OUTPUT,*APP_OUTPUTS]:
    b=backup(output)
    if b:
        backups.append(b)
    write_csv(output,rows)
linked=sum(1 for row in rows if row["sourceNodeId"])
print()
print("Living Notitia")
print("publish_confirmed_places.py")
print()
print("Match input            :",MATCH_INPUT)
print("Matched rows in input  :",len(matches))
print("Published map rows     :",len(rows))
print("Without coordinates    :",len(without_coordinates))
print("Linked to SourceNode   :",linked)
print("Without SourceNode link:",len(rows)-linked)
print("SourceNode file        :",source_file or "(not found)")
print()
print("Confirmed audit file   :",CONFIRMED_OUTPUT)
for output in APP_OUTPUTS:
    print("Web-app Places file    :",output)
if backups:
    print()
    print("Backups:")
    for path in backups:
        print(" ",path)
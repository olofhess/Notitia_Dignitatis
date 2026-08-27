#
# Living Notitia V3
# build_place_gazetteer.py
#
#!/usr/bin/env python3
from pathlib import Path
import csv
import shutil
from datetime import datetime
HERE=Path(__file__).resolve()
ROOT=next((p for p in HERE.parents if (p/"csv"/"PlaceMatch_context.csv").exists()),None)
if ROOT is None:
    raise FileNotFoundError("Kan inte hitta projektroten med csv/PlaceMatch_context.csv")
MATCH_INPUT=ROOT/"csv"/"PlaceMatch_context.csv"
PLEIADES_INPUT=ROOT/"csv"/"PleiadesPlace.csv"
OUTPUT=ROOT/"csv"/"PlaceGazetteer.csv"
FIELDS=[
    "gazetteerId",
    "placeName",
    "sourcePlaceName",
    "pleiadesId",
    "pleiadesName",
    "latitude",
    "longitude",
    "featureType",
    "description",
    "uri",
    "confidence"
]
def clean(value):
    return str(value or "").strip()
def load_csv(path):
    with path.open(newline="",encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))
pleiades_index={}
for row in load_csv(PLEIADES_INPUT):
    pid=clean(row.get("pleiadesId"))
    if pid:
        pleiades_index[pid]=row
rows=[]
seen=set()
missing_pleiades=0
for match in load_csv(MATCH_INPUT):
    pid=clean(match.get("pleiadesId"))
    source_name=clean(match.get("placeName"))
    candidate=clean(match.get("candidate")) or source_name
    if not pid or not source_name:
        continue
    duplicate_key=(source_name.casefold(),pid)
    if duplicate_key in seen:
        continue
    seen.add(duplicate_key)
    pleiades=pleiades_index.get(pid)
    if pleiades is None:
        missing_pleiades+=1
        pleiades={}
    latitude=clean(match.get("latitude")) or clean(pleiades.get("latitude"))
    longitude=clean(match.get("longitude")) or clean(pleiades.get("longitude"))
    rows.append({
        "gazetteerId":"",
        "placeName":candidate,
        "sourcePlaceName":source_name,
        "pleiadesId":pid,
        "pleiadesName":clean(match.get("pleiadesName")) or clean(pleiades.get("title")),
        "latitude":latitude,
        "longitude":longitude,
        "featureType":clean(match.get("featureType")) or clean(pleiades.get("featureType")),
        "description":clean(pleiades.get("description")),
        "uri":clean(pleiades.get("uri")),
        "confidence":"confirmed"
    })
rows.sort(key=lambda r:(r["placeName"].casefold(),r["pleiadesId"]))
for number,row in enumerate(rows,1):
    row["gazetteerId"]=f"GAZ{number:05d}"
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
if OUTPUT.exists():
    archive=OUTPUT.parent/"archive"
    archive.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
    backup=archive/f"PlaceGazetteer_{stamp}.csv"
    shutil.copy2(OUTPUT,backup)
else:
    backup=None
with OUTPUT.open("w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
with_coordinates=sum(1 for row in rows if row["latitude"] and row["longitude"])
without_coordinates=len(rows)-with_coordinates
print()
print("Living Notitia V3")
print("build_place_gazetteer.py")
print()
print("Confirmed match rows :",len(load_csv(MATCH_INPUT)))
print("Gazetteer places      :",len(rows))
print("With coordinates      :",with_coordinates)
print("Without coordinates   :",without_coordinates)
print("Missing Pleiades rows :",missing_pleiades)
print()
print("Output :",OUTPUT)
if backup:
    print("Backup :",backup)
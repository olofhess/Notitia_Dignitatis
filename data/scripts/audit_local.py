from pathlib import Path
import csv
from collections import Counter,defaultdict
HERE=Path(__file__).resolve()
ROOT=next((p for p in [HERE.parent,*HERE.parents] if (p/"csv"/"PlaceMatch_context.csv").exists()),None)
if ROOT is None:
    raise FileNotFoundError("Kan inte hitta csv/PlaceMatch_context.csv")
FILES={
"MATCH":ROOT/"csv"/"PlaceMatch_context.csv",
"AMBIGUOUS":ROOT/"csv"/"PlaceAmbiguous_context.csv",
"UNMATCHED":ROOT/"csv"/"PlaceUnmatched_context.csv"
}
def read(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))
def source(row):
    return (row.get("placeSource") or "").strip().lower()
def context(row):
    return " ".join([
        row.get("chapter","") or "",
        row.get("contextText","") or "",
        row.get("declaredProvince","") or "",
        row.get("hardProvince","") or "",
        row.get("softProvince","") or "",
        row.get("region","") or ""
    ]).lower()
def has_coords(row):
    try:
        float(row.get("latitude",""))
        float(row.get("longitude",""))
        return True
    except:
        return False
rows={k:read(v) for k,v in FILES.items()}
sources=["limes","castris","prope"]
print()
print("Living Notitia V3")
print("audit_v10_new_geography.py")
print()
print("NEW GEOGRAPHY BY SOURCE")
for s in sources:
    print()
    print(s.upper())
    for status in ["MATCH","AMBIGUOUS","UNMATCHED"]:
        rr=[r for r in rows[status] if source(r)==s]
        coords=sum(has_coords(r) for r in rr)
        print(f"  {status:<10} {len(rr):3d}   with coordinates {coords:3d}")
print()
print("AFRICA / TRIPOLITANA")
for status in ["MATCH","AMBIGUOUS","UNMATCHED"]:
    rr=[r for r in rows[status] if ("africa" in context(r) or "tripolitan" in context(r)) and source(r) in sources]
    print()
    print(status,len(rr))
    seen=set()
    for r in rr:
        key=(r.get("occurrenceId",""),r.get("placeName",""),r.get("pleiadesId",""))
        if key in seen:
            continue
        seen.add(key)
        print(" ",r.get("placeName",""),"|",source(r),"|",r.get("pleiadesId",""),"|",r.get("pleiadesName",""),"|",r.get("latitude",""),r.get("longitude",""),"|",r.get("matchType",""))
print()
print("GERMANIA II")
for status in ["MATCH","AMBIGUOUS","UNMATCHED"]:
    rr=[r for r in rows[status] if "germaniae secundae" in context(r) or "germania ii" in context(r)]
    if not rr:
        continue
    print()
    print(status,len(rr))
    seen=set()
    for r in rr:
        key=(r.get("occurrenceId",""),r.get("placeName",""),r.get("pleiadesId",""))
        if key in seen:
            continue
        seen.add(key)
        print(" ",r.get("placeName",""),"|",source(r),"|",r.get("pleiadesId",""),"|",r.get("pleiadesName",""),"|",r.get("latitude",""),r.get("longitude",""),"|",r.get("matchType",""))
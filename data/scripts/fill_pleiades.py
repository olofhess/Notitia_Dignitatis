from pathlib import Path
import csv
import json
import shutil
from datetime import datetime
HERE=Path(__file__).resolve()
def find_root():
    for p in [HERE.parent,*HERE.parents]:
        if (p/"csv"/"PleiadesPlace.csv").exists():
            return p
    raise FileNotFoundError("Kan inte hitta projektroten med csv/PleiadesPlace.csv")
ROOT=find_root()
CSV_PATH=ROOT/"csv"/"PleiadesPlace.csv"
JSON_CANDIDATES=[
    ROOT/"pleiades-places.json",
    ROOT/"data"/"pleiades-places.json",
    ROOT/"data"/"pleiades"/"pleiades-places.json",
    ROOT/"data"/"gazetteer"/"pleiades-places.json",
    ROOT/"pleiades"/"pleiades-places.json"
]
JSON_PATH=next((p for p in JSON_CANDIDATES if p.exists()),None)
if JSON_PATH is None:
    found=list(ROOT.rglob("pleiades-places.json"))
    if found:
        JSON_PATH=max(found,key=lambda p:p.stat().st_size)
if JSON_PATH is None:
    raise FileNotFoundError("Kan inte hitta den lokala filen pleiades-places.json under projektroten")
def iter_pleiades_graph(path,chunk_size=1024*1024):
    decoder=json.JSONDecoder()
    with path.open("r",encoding="utf-8") as f:
        buf=""
        graph_found=False
        eof=False
        while not graph_found:
            chunk=f.read(chunk_size)
            if not chunk:
                raise ValueError('Kan inte hitta "@graph" i pleiades-places.json')
            buf+=chunk
            marker=buf.find('"@graph"')
            if marker<0:
                buf=buf[-128:]
                continue
            bracket=buf.find("[",marker)
            while bracket<0:
                chunk=f.read(chunk_size)
                if not chunk:
                    raise ValueError('Kan inte hitta arrayen efter "@graph"')
                buf+=chunk
                bracket=buf.find("[",marker)
            buf=buf[bracket+1:]
            graph_found=True
        pos=0
        while True:
            while True:
                while pos<len(buf) and (buf[pos].isspace() or buf[pos]==","):
                    pos+=1
                if pos<len(buf):
                    if buf[pos]=="]":
                        return
                    break
                chunk=f.read(chunk_size)
                if not chunk:
                    return
                buf=buf[pos:]+chunk
                pos=0
            try:
                obj,end=decoder.raw_decode(buf,pos)
            except json.JSONDecodeError:
                chunk=f.read(chunk_size)
                if not chunk:
                    raise
                buf=buf[pos:]+chunk
                pos=0
                continue
            yield obj
            pos=end
            if pos>4*chunk_size:
                buf=buf[pos:]
                pos=0
def clean(value):
    return str(value or "").strip()
with CSV_PATH.open("r",encoding="utf-8-sig",newline="") as f:
    reader=csv.DictReader(f)
    fieldnames=list(reader.fieldnames or [])
    rows=list(reader)
required={"pleiadesId","latitude","longitude"}
missing=required-set(fieldnames)
if missing:
    raise RuntimeError("PleiadesPlace.csv saknar kolumner: "+", ".join(sorted(missing)))
by_id={}
for row in rows:
    pid=clean(row.get("pleiadesId"))
    if pid:
        by_id[pid]=row
before_missing=sum(1 for r in rows if not clean(r.get("latitude")) or not clean(r.get("longitude")))
targets={"334577","334578","334579","334580","299007"}
target_before={pid:(clean(by_id.get(pid,{}).get("latitude")),clean(by_id.get(pid,{}).get("longitude"))) for pid in targets}
json_objects=0
reprpoints=0
filled_rows=0
filled_ids=set()
existing_unchanged=0
for obj in iter_pleiades_graph(JSON_PATH):
    json_objects+=1
    if not isinstance(obj,dict):
        continue
    pid=clean(obj.get("id"))
    if not pid or pid not in by_id:
        continue
    rp=obj.get("reprPoint")
    if not (isinstance(rp,list) and len(rp)>=2):
        continue
    try:
        lon=float(rp[0])
        lat=float(rp[1])
    except (TypeError,ValueError):
        continue
    reprpoints+=1
    row=by_id[pid]
    old_lat=clean(row.get("latitude"))
    old_lon=clean(row.get("longitude"))
    changed=False
    if not old_lat:
        row["latitude"]=format(lat,".12g")
        changed=True
    if not old_lon:
        row["longitude"]=format(lon,".12g")
        changed=True
    if changed:
        filled_rows+=1
        filled_ids.add(pid)
    else:
        existing_unchanged+=1
archive=ROOT/"csv"/"archive"
archive.mkdir(parents=True,exist_ok=True)
stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
backup=archive/f"PleiadesPlace_{stamp}.csv"
shutil.copy2(CSV_PATH,backup)
temp=CSV_PATH.with_suffix(".csv.tmp")
with temp.open("w",encoding="utf-8",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=fieldnames,extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
temp.replace(CSV_PATH)
after_missing=sum(1 for r in rows if not clean(r.get("latitude")) or not clean(r.get("longitude")))
print()
print("Living Notitia V3")
print("fill_pleiades.py")
print()
print("Local JSON             :",JSON_PATH)
print("PleiadesPlace rows     :",len(rows))
print("JSON objects read      :",json_objects)
print("reprPoint records      :",reprpoints)
print("Rows filled            :",filled_rows)
print("Missing before         :",before_missing)
print("Missing after          :",after_missing)
print("Existing coords kept   :",existing_unchanged)
print("Backup                 :",backup)
print()
print("Control IDs:")
for pid in sorted(targets):
    row=by_id.get(pid,{})
    before=target_before.get(pid,("",""))
    after=(clean(row.get("latitude")),clean(row.get("longitude")))
    mark="FILLED" if pid in filled_ids else "unchanged"
    print(f"  {pid}: {before[0]},{before[1]} -> {after[0]},{after[1]}  {mark}")
print()
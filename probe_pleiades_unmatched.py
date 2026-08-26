#
# Living Notitia
# #
# Living Notitia
# probe_pleiades_unmatched.py
#
from pathlib import Path
import csv
import json
import re
import unicodedata
import difflib
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[0]
MATCHES=ROOT/"csv"/"PleiadesMatch.csv"
PLEIADES=ROOT/"data"/"pleiades-places.json"
OUTPUT=ROOT/"csv"/"PleiadesNearMatch.csv"
CHAPTERS={
    "Dux Britanniarum",
    "Dux Daciae ripensis"
}
TOP_N=5
CUTOFF=0.55
def normalize(text):
    if not text:
        return ""
    text=unicodedata.normalize("NFKD",str(text))
    text="".join(
        c for c in text
        if not unicodedata.combining(c)
    )
    text=text.lower().strip()
    text=text.replace("j","i")
    text=text.replace("u","v")
    text=re.sub(r"[.,;:()\[\]{}\'’\"*/?]"," ",text)
    text=re.sub(r"\s+"," ",text)
    return text
def exploratory_variants(name):
    n=normalize(name)
    variants={n}
    if n.endswith("o") and len(n)>3:
        variants.add(n[:-1]+"um")
    if n.endswith("ae") and len(n)>4:
        variants.add(n[:-2]+"a")
        variants.add(n[:-2]+"um")
    if n.endswith("i") and len(n)>4:
        variants.add(n[:-1]+"um")
        variants.add(n[:-1]+"us")
    if n.endswith("is") and len(n)>5:
        variants.add(n[:-2]+"um")
        variants.add(n[:-2]+"a")
    if n.endswith("a") and len(n)>5:
        variants.add(n[:-1]+"um")
    return variants
def collect_names(place):
    if not isinstance(place,dict):
        return []
    props=place.get("properties",place)
    pid=(
        place.get("id")
        or props.get("id")
        or props.get("uri")
        or ""
    )
    title=props.get("title") or ""
    names=set()
    if title:
        names.add(str(title))
    for key in [
        "name",
        "nameAttested",
        "nameRomanized",
        "attested",
        "romanized"
    ]:
        value=props.get(key)
        if isinstance(value,str):
            names.add(value)
        elif isinstance(value,list):
            for item in value:
                if isinstance(item,str):
                    names.add(item)
    raw_names=props.get("names",[])
    if isinstance(raw_names,list):
        for item in raw_names:
            if isinstance(item,str):
                names.add(item)
            elif isinstance(item,dict):
                for key in [
                    "nameAttested",
                    "nameRomanized",
                    "attested",
                    "romanized"
                ]:
                    value=item.get(key)
                    if isinstance(value,str):
                        names.add(value)
                    elif isinstance(value,list):
                        for x in value:
                            if x:
                                names.add(str(x))
    result=[]
    for name in names:
        key=normalize(name)
        if key:
            result.append({
                "id":str(pid),
                "title":str(title or name),
                "name":str(name),
                "key":key
            })
    return result
print()
print("Living Notitia")
print("probe_pleiades_unmatched.py")
print()
with open(MATCHES,encoding="utf-8") as f:
    rows=list(csv.DictReader(f))
targets=[]
seen=set()
for row in rows:
    if row.get("chapter") not in CHAPTERS:
        continue
    if row.get("status")!="UNMATCHED":
        continue
    name=row.get("placeName","").strip()
    if not name:
        continue
    key=(row.get("chapter",""),name)
    if key in seen:
        continue
    seen.add(key)
    targets.append(row)
print("Unmatched target names:",len(targets))
print("Reading Pleiades:",PLEIADES)
with open(PLEIADES,encoding="utf-8") as f:
    data=json.load(f)
if isinstance(data,dict) and "@graph" in data:
    places=data["@graph"]
elif isinstance(data,dict) and "features" in data:
    places=data["features"]
elif isinstance(data,list):
    places=data
else:
    places=[]
name_index=defaultdict(list)
for place in places:
    for record in collect_names(place):
        name_index[record["key"]].append(record)
all_keys=list(name_index.keys())
print("Indexed names:",len(all_keys))
output=[]
for row in targets:
    place_name=row.get("placeName","").strip()
    chapter=row.get("chapter","")
    exact_variant_hits=[]
    for variant in exploratory_variants(place_name):
        if variant==normalize(place_name):
            continue
        for record in name_index.get(variant,[]):
            exact_variant_hits.append((variant,record))
    unique_ids=set()
    rank=0
    for variant,record in exact_variant_hits:
        if record["id"] in unique_ids:
            continue
        unique_ids.add(record["id"])
        rank+=1
        output.append({
            "chapter":chapter,
            "placeName":place_name,
            "rank":rank,
            "method":"VARIANT_EXACT",
            "score":"1.000",
            "searchForm":variant,
            "pleiadesId":record["id"],
            "pleiadesTitle":record["title"],
            "matchedName":record["name"]
        })
        if rank>=TOP_N:
            break
    if rank>=TOP_N:
        continue
    search_key=normalize(place_name)
    close_keys=difflib.get_close_matches(
        search_key,
        all_keys,
        n=30,
        cutoff=CUTOFF
    )
    for close_key in close_keys:
        score=difflib.SequenceMatcher(
            None,
            search_key,
            close_key
        ).ratio()
        for record in name_index[close_key]:
            if record["id"] in unique_ids:
                continue
            unique_ids.add(record["id"])
            rank+=1
            output.append({
                "chapter":chapter,
                "placeName":place_name,
                "rank":rank,
                "method":"NEAR",
                "score":f"{score:.3f}",
                "searchForm":search_key,
                "pleiadesId":record["id"],
                "pleiadesTitle":record["title"],
                "matchedName":record["name"]
            })
            if rank>=TOP_N:
                break
        if rank>=TOP_N:
            break
fields=[
    "chapter",
    "placeName",
    "rank",
    "method",
    "score",
    "searchForm",
    "pleiadesId",
    "pleiadesTitle",
    "matchedName"
]
with open(
    OUTPUT,
    "w",
    newline="",
    encoding="utf-8"
) as f:
    writer=csv.DictWriter(
        f,
        fieldnames=fields
    )
    writer.writeheader()
    writer.writerows(output)
print()
for chapter in sorted(CHAPTERS):
    count=sum(
        1 for row in targets
        if row.get("chapter")==chapter
    )
    print(chapter,":",count,"unmatched names")
print()
print("Output:",OUTPUT)
#
from pathlib import Path
import csv
import json
import re
import unicodedata
import difflib
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[0]
MATCHES=ROOT/"csv"/"PleiadesMatch.csv"
PLEIADES=ROOT/"data"/"pleiades-places.json"
OUTPUT=ROOT/"csv"/"PleiadesNearMatch.csv"
CHAPTERS={
    "Dux Britanniarum",
    "Dux Daciae ripensis"
}
TOP_N=5
CUTOFF=0.55
def normalize(text):
    if not text:
        return ""
    text=unicodedata.normalize("NFKD",str(text))
    text="".join(
        c for c in text
        if not unicodedata.combining(c)
    )
    text=text.lower().strip()
    text=text.replace("j","i")
    text=text.replace("u","v")
    text=re.sub(r"[.,;:()\[\]{}\'’\"*/?]"," ",text)
    text=re.sub(r"\s+"," ",text)
    return text
def exploratory_variants(name):
    n=normalize(name)
    variants={n}
    if n.endswith("o") and len(n)>3:
        variants.add(n[:-1]+"um")
    if n.endswith("ae") and len(n)>4:
        variants.add(n[:-2]+"a")
        variants.add(n[:-2]+"um")
    if n.endswith("i") and len(n)>4:
        variants.add(n[:-1]+"um")
        variants.add(n[:-1]+"us")
    if n.endswith("is") and len(n)>5:
        variants.add(n[:-2]+"um")
        variants.add(n[:-2]+"a")
    if n.endswith("a") and len(n)>5:
        variants.add(n[:-1]+"um")
    return variants
def collect_names(place):
    if not isinstance(place,dict):
        return []
    props=place.get("properties",place)
    pid=(
        place.get("id")
        or props.get("id")
        or props.get("uri")
        or ""
    )
    title=props.get("title") or ""
    names=set()
    if title:
        names.add(str(title))
    for key in [
        "name",
        "nameAttested",
        "nameRomanized",
        "attested",
        "romanized"
    ]:
        value=props.get(key)
        if isinstance(value,str):
            names.add(value)
        elif isinstance(value,list):
            for item in value:
                if isinstance(item,str):
                    names.add(item)
    raw_names=props.get("names",[])
    if isinstance(raw_names,list):
        for item in raw_names:
            if isinstance(item,str):
                names.add(item)
            elif isinstance(item,dict):
                for key in [
                    "nameAttested",
                    "nameRomanized",
                    "attested",
                    "romanized"
                ]:
                    value=item.get(key)
                    if isinstance(value,str):
                        names.add(value)
                    elif isinstance(value,list):
                        for x in value:
                            if x:
                                names.add(str(x))
    result=[]
    for name in names:
        key=normalize(name)
        if key:
            result.append({
                "id":str(pid),
                "title":str(title or name),
                "name":str(name),
                "key":key
            })
    return result
print()
print("Living Notitia")
print("probe_pleiades_unmatched.py")
print()
with open(MATCHES,encoding="utf-8") as f:
    rows=list(csv.DictReader(f))
targets=[]
seen=set()
for row in rows:
    if row.get("chapter") not in CHAPTERS:
        continue
    if row.get("status")!="UNMATCHED":
        continue
    name=row.get("placeName","").strip()
    if not name:
        continue
    key=(row.get("chapter",""),name)
    if key in seen:
        continue
    seen.add(key)
    targets.append(row)
print("Unmatched target names:",len(targets))
print("Reading Pleiades:",PLEIADES)
with open(PLEIADES,encoding="utf-8") as f:
    data=json.load(f)
if isinstance(data,dict) and "@graph" in data:
    places=data["@graph"]
elif isinstance(data,dict) and "features" in data:
    places=data["features"]
elif isinstance(data,list):
    places=data
else:
    places=[]
name_index=defaultdict(list)
for place in places:
    for record in collect_names(place):
        name_index[record["key"]].append(record)
all_keys=list(name_index.keys())
print("Indexed names:",len(all_keys))
output=[]
for row in targets:
    place_name=row.get("placeName","").strip()
    chapter=row.get("chapter","")
    exact_variant_hits=[]
    for variant in exploratory_variants(place_name):
        if variant==normalize(place_name):
            continue
        for record in name_index.get(variant,[]):
            exact_variant_hits.append((variant,record))
    unique_ids=set()
    rank=0
    for variant,record in exact_variant_hits:
        if record["id"] in unique_ids:
            continue
        unique_ids.add(record["id"])
        rank+=1
        output.append({
            "chapter":chapter,
            "placeName":place_name,
            "rank":rank,
            "method":"VARIANT_EXACT",
            "score":"1.000",
            "searchForm":variant,
            "pleiadesId":record["id"],
            "pleiadesTitle":record["title"],
            "matchedName":record["name"]
        })
        if rank>=TOP_N:
            break
    if rank>=TOP_N:
        continue
    search_key=normalize(place_name)
    close_keys=difflib.get_close_matches(
        search_key,
        all_keys,
        n=30,
        cutoff=CUTOFF
    )
    for close_key in close_keys:
        score=difflib.SequenceMatcher(
            None,
            search_key,
            close_key
        ).ratio()
        for record in name_index[close_key]:
            if record["id"] in unique_ids:
                continue
            unique_ids.add(record["id"])
            rank+=1
            output.append({
                "chapter":chapter,
                "placeName":place_name,
                "rank":rank,
                "method":"NEAR",
                "score":f"{score:.3f}",
                "searchForm":search_key,
                "pleiadesId":record["id"],
                "pleiadesTitle":record["title"],
                "matchedName":record["name"]
            })
            if rank>=TOP_N:
                break
        if rank>=TOP_N:
            break
fields=[
    "chapter",
    "placeName",
    "rank",
    "method",
    "score",
    "searchForm",
    "pleiadesId",
    "pleiadesTitle",
    "matchedName"
]
with open(
    OUTPUT,
    "w",
    newline="",
    encoding="utf-8"
) as f:
    writer=csv.DictWriter(
        f,
        fieldnames=fields
    )
    writer.writeheader()
    writer.writerows(output)
print()
for chapter in sorted(CHAPTERS):
    count=sum(
        1 for row in targets
        if row.get("chapter")==chapter
    )
    print(chapter,":",count,"unmatched names")
print()
print("Output:",OUTPUT)
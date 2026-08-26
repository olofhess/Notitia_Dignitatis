#
# Living Notitia V3
# match_notitia_pleiades_local.py
#
from pathlib import Path
import csv
import json
import math
import re
import unicodedata
from collections import defaultdict,Counter
HERE=Path(__file__).resolve()
def find_root():
    for p in [HERE.parent,*HERE.parents]:
        if (p/"csv"/"PleiadesName.csv").exists() or (p/"data"/"work"/"SemanticNode.csv").exists():
            return p
    raise FileNotFoundError("Kan inte hitta projektroten")
ROOT=find_root()
def first_existing(paths,required=True):
    for path in paths:
        if path.exists():
            return path
    if required:
        raise FileNotFoundError("Kan inte hitta någon av: "+", ".join(str(p) for p in paths))
    return None
SOURCE_INPUT=first_existing([
    ROOT/"data"/"work"/"SemanticNode.csv",
    ROOT/"csv"/"SemanticNode.csv",
    ROOT/"SemanticNode.csv",
    ROOT/"csv"/"Place.csv"
])
PLEIADES_NAME_INPUT=first_existing([
    ROOT/"csv"/"PleiadesName.csv",
    ROOT/"data"/"PleiadesName.csv"
])
PLEIADES_PLACE_INPUT=first_existing([
    ROOT/"csv"/"PleiadesPlace.csv",
    ROOT/"data"/"PleiadesPlace.csv"
])
PROVINCE_MATCH_INPUT=first_existing([
    ROOT/"csv"/"ProvinceMatch.csv",
    ROOT/"data"/"ProvinceMatch.csv",
    ROOT/"data"/"work"/"ProvinceMatch.csv"
],required=False)
GEOJSON_INPUT=first_existing([
    ROOT/"data"/"geojson_prov"/"provinces.geojson",
    ROOT/"geojson_prov"/"provinces.geojson",
    ROOT/"data"/"provinces.geojson"
])
OUTPUT_DIR=ROOT/"csv"
MATCH_OUTPUT=OUTPUT_DIR/"PlaceMatch_context.csv"
AMBIGUOUS_OUTPUT=OUTPUT_DIR/"PlaceAmbiguous_context.csv"
UNMATCHED_OUTPUT=OUTPUT_DIR/"PlaceUnmatched_context.csv"
REJECTED_OUTPUT=OUTPUT_DIR/"PlaceRejected_context.csv"
MAX_EDIT_DISTANCE=2
MIN_FUZZY_SIMILARITY=0.86
AUTO_FUZZY_SIMILARITY=0.90
MIN_FUZZY_MARGIN=0.06
NON_POINT_TYPES={"river","island","mountain","road","region","province","sea","water"}
def clean(text):
    text=str(text or "")
    text=unicodedata.normalize("NFKD",text)
    text="".join(ch for ch in text if not unicodedata.combining(ch))
    text=text.replace("æ","ae").replace("Æ","Ae")
    text=re.sub(r"^\(.*?\)\s*","",text)
    text=re.sub(r"^\.+\s*","",text)
    text=" ".join(text.split())
    return text.strip(" .,;:-()[]")
def norm(text):
    text=clean(text).lower()
    text=re.sub(r"[^a-z0-9]+"," ",text)
    return " ".join(text.split())
def latin_key(text):
    text=norm(text)
    text=text.replace("j","i").replace("v","u").replace("y","i")
    text=text.replace("ph","f").replace("th","t").replace("ch","c")
    text=text.replace("ae","e").replace("oe","e")
    return text.replace(" ","")
def levenshtein(a,b,limit=None):
    if a==b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if limit is not None and abs(len(a)-len(b))>limit:
        return limit+1
    if len(a)>len(b):
        a,b=b,a
    previous=list(range(len(a)+1))
    for j,cb in enumerate(b,1):
        current=[j]
        row_min=j
        for i,ca in enumerate(a,1):
            value=min(current[i-1]+1,previous[i]+1,previous[i-1]+(ca!=cb))
            current.append(value)
            row_min=min(row_min,value)
        if limit is not None and row_min>limit:
            return limit+1
        previous=current
    return previous[-1]
def similarity(a,b):
    a=latin_key(a)
    b=latin_key(b)
    if not a or not b:
        return 0.0
    d=levenshtein(a,b)
    return 1.0-d/max(len(a),len(b))
def detect_delimiter(path):
    with path.open(encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                return ";" if line.count(";")>line.count(",") else ","
    return ","
def load_csv(path):
    delimiter=detect_delimiter(path)
    with path.open(newline="",encoding="utf-8-sig") as f:
        return list(csv.DictReader(f,delimiter=delimiter))
def get(row,*names):
    for name in names:
        value=clean(row.get(name,""))
        if value:
            return value
    return ""
def explicit_province(place_name):
    m=re.search(r"\bin\s+(.+)$",clean(place_name),flags=re.I)
    return clean(m.group(1)) if m else ""
def case_variants(text):
    text=clean(text)
    if not text:
        return []
    words=text.split()
    last=words[-1]
    prefix=" ".join(words[:-1])
    lower_last=last.lower()
    result=[text]
    def add(new_last):
        value=(prefix+" "+new_last).strip()
        if value not in result:
            result.append(value)
    if lower_last.endswith("iae") and len(last)>4:
        add(last[:-3]+"ia")
    if lower_last.endswith("ae") and len(last)>3:
        add(last[:-1])
    if lower_last.endswith("am") and len(last)>3:
        add(last[:-1])
    if lower_last.endswith("as") and len(last)>3:
        add(last[:-2]+"ae")
        add(last[:-1])
    if lower_last.endswith("io") and len(last)>3:
        add(last[:-2]+"ium")
    if lower_last.endswith("o") and len(last)>3:
        add(last[:-1]+"um")
        add(last[:-1]+"us")
        add(last[:-1]+"os")
    if lower_last.endswith("i") and len(last)>3:
        add(last[:-1]+"us")
        add(last[:-1]+"um")
        add(last+"s")
        add(last+"o")
    if lower_last.endswith("em") and len(last)>4:
        add(last[:-2]+"is")
        add(last[:-2]+"es")
    if lower_last.endswith("e") and len(last)>4:
        add(last[:-1]+"is")
    if lower_last.endswith("is") and len(last)>4:
        add(last[:-2]+"ae")
        add(last[:-2]+"es")
    return result
def candidate_variants(place_name):
    result=[]
    seen=set()
    def add(value,rule,tier):
        value=clean(value)
        key=norm(value)
        if not key or key in seen:
            return
        seen.add(key)
        result.append((value,rule,tier))
    add(place_name,"original",0)
    m=re.match(r"^(apud|ad|contra|prope|iuxta)\s+(.+)$",place_name,flags=re.I)
    if m:
        add(m.group(2),"strip_preposition",0)
    m=re.match(r"^(.+?)\s+in\s+.+$",place_name,flags=re.I)
    if m:
        add(m.group(1),"before_in",0)
    for splitter in [r"\s+siue\s+",r"\s+sive\s+",r"\s+-\s+"]:
        pieces=re.split(splitter,place_name,flags=re.I)
        if len(pieces)>1:
            for piece in pieces:
                add(piece,"alias",0)
    for value,rule,tier in list(result):
        for case_value in case_variants(value):
            if norm(case_value)!=norm(value):
                add(case_value,rule+"_case",tier)
    for value,rule,tier in list(result):
        words=value.split()
        if len(words)>1:
            add(words[0],"first_word",1)
            for case_value in case_variants(words[0]):
                if norm(case_value)!=norm(words[0]):
                    add(case_value,"first_word_case",1)
    return result
def to_float(value):
    try:
        number=float(str(value).strip().replace(",","."))
    except (TypeError,ValueError):
        return None
    return number if math.isfinite(number) else None
def point_on_segment(x,y,x1,y1,x2,y2,eps=1e-10):
    cross=(x-x1)*(y2-y1)-(y-y1)*(x2-x1)
    if abs(cross)>eps:
        return False
    return min(x1,x2)-eps<=x<=max(x1,x2)+eps and min(y1,y2)-eps<=y<=max(y1,y2)+eps
def point_in_ring(x,y,ring):
    inside=False
    if len(ring)<3:
        return False
    j=len(ring)-1
    for i in range(len(ring)):
        x1,y1=ring[j][0],ring[j][1]
        x2,y2=ring[i][0],ring[i][1]
        if point_on_segment(x,y,x1,y1,x2,y2):
            return True
        if (y1>y)!=(y2>y):
            cross_x=x1+(y-y1)*(x2-x1)/(y2-y1)
            if x<cross_x:
                inside=not inside
        j=i
    return inside
def point_in_polygon(x,y,polygon):
    if not polygon or not point_in_ring(x,y,polygon[0]):
        return False
    return not any(point_in_ring(x,y,hole) for hole in polygon[1:])
def point_in_geometry(x,y,geometry):
    if not geometry:
        return False
    kind=geometry.get("type","")
    coords=geometry.get("coordinates",[])
    if kind=="Polygon":
        return point_in_polygon(x,y,coords)
    if kind=="MultiPolygon":
        return any(point_in_polygon(x,y,p) for p in coords)
    return False
def feature_name(feature):
    p=feature.get("properties",{})
    return clean(p.get("PROV_NAME") or p.get("prov_name") or p.get("NAME") or p.get("name") or p.get("PROVINCE") or p.get("province"))
def feature_id(feature):
    p=feature.get("properties",{})
    return clean(p.get("geojsonId") or p.get("GEOJSONID") or p.get("id") or feature.get("id",""))
def province_tokens(text):
    stop={"et","in","provincia","provinciae","pars","prima","primae","secunda","secundae","superior","superioris","inferior","inferioris"}
    return [t for t in norm(text).split() if t not in stop and len(t)>2]
def province_compatible(expected,actual,alias_targets):
    if not expected or not actual:
        return False
    ne=norm(expected)
    na=norm(actual)
    if ne==na or ne in na or na in ne:
        return True
    targets=alias_targets.get(ne,set())
    if na in targets:
        return True
    e_tokens=province_tokens(expected)
    a_tokens=province_tokens(actual)
    for e in e_tokens:
        for a in a_tokens:
            if e==a or e in a or a in e or similarity(e,a)>=0.82:
                return True
    return similarity(expected,actual)>=0.80
def is_non_point(feature_type):
    words=set(norm(feature_type).split())
    return bool(words & NON_POINT_TYPES)
source_rows=load_csv(SOURCE_INPUT)
name_rows=load_csv(PLEIADES_NAME_INPUT)
place_rows=load_csv(PLEIADES_PLACE_INPUT)
with GEOJSON_INPUT.open(encoding="utf-8") as f:
    geojson=json.load(f)
features=[f for f in geojson.get("features",[]) if f.get("geometry",{}).get("type") in {"Polygon","MultiPolygon"}]
alias_targets=defaultdict(set)
if PROVINCE_MATCH_INPUT:
    for row in load_csv(PROVINCE_MATCH_INPUT):
        target=get(row,"gisProvince","canonicalName","geoName")
        aliases={get(row,"notitiaMatch"),get(row,"canonicalName"),get(row,"gisProvince"),get(row,"geoName")}
        target_norm=norm(target)
        if not target_norm:
            continue
        for alias in aliases:
            if alias:
                alias_targets[norm(alias)].add(target_norm)
place_by_id={}
for row in place_rows:
    pid=get(row,"pleiadesId","id")
    if pid:
        place_by_id[pid]=row
exact_index=defaultdict(dict)
fuzzy_names={}
for row in name_rows:
    pid=get(row,"pleiadesId","id")
    pname=get(row,"romanized","name","title")
    if not pid or not pname:
        continue
    exact_index[norm(pname)][pid]=pname
    key=latin_key(pname)
    if key:
        fuzzy_names[(pid,key)]=pname
fuzzy_buckets=defaultdict(list)
for (pid,key),pname in fuzzy_names.items():
    fuzzy_buckets[(key[0],len(key))].append((pid,pname,key))
def occurrence_rows(rows):
    result=[]
    seen=set()
    for i,row in enumerate(rows,1):
        semantic_type=norm(get(row,"semanticType","type"))
        semantic_class=norm(get(row,"semanticClass","class"))
        source_id=get(row,"sourceNodeId","nodeId","officeId") or f"ROW{i:06d}"
        if "semanticType" in row or "semanticClass" in row:
            if semantic_type not in {"placename","place"} and semantic_class!="place":
                continue
            name=get(row,"canonicalName","value","placeName","latinName")
        else:
            name=get(row,"placeName","latinName","canonicalName")
        if not name:
            continue
        province=get(row,"contextProvince","province","currentProvince")
        region=get(row,"contextRegion","region","currentRegion")
        text=get(row,"text","sourceText","context")
        key=(source_id,norm(name))
        if key in seen:
            continue
        seen.add(key)
        result.append({"sourceNodeId":source_id,"placeName":name,"province":province,"region":region,"text":text})
    return result
occurrences=occurrence_rows(source_rows)
def containing_province(latitude,longitude):
    lat=to_float(latitude)
    lon=to_float(longitude)
    if lat is None or lon is None:
        return "",""
    for feature in features:
        if point_in_geometry(lon,lat,feature.get("geometry")):
            return feature_name(feature),feature_id(feature)
    return "",""
province_cache={}
def candidate_info(pid,pname,candidate,rule,tier,name_similarity):
    place=place_by_id.get(pid,{})
    lat=get(place,"latitude","lat")
    lon=get(place,"longitude","lon","lng")
    feature_type=get(place,"featureType","type")
    cache_key=(lat,lon)
    if cache_key not in province_cache:
        province_cache[cache_key]=containing_province(lat,lon)
    gis_province,geojson_id=province_cache[cache_key]
    return {"pleiadesId":pid,"pleiadesName":pname,"candidate":candidate,"rule":rule,"tier":tier,"nameSimilarity":name_similarity,"latitude":lat,"longitude":lon,"featureType":feature_type,"gisProvince":gis_province,"geojsonId":geojson_id}
def exact_candidates(name):
    found={}
    for candidate,rule,tier in candidate_variants(name):
        for pid,pname in exact_index.get(norm(candidate),{}).items():
            item=candidate_info(pid,pname,candidate,rule,tier,1.0)
            old=found.get(pid)
            if old is None or (item["tier"],len(item["candidate"]))<(old["tier"],len(old["candidate"])):
                found[pid]=item
    return list(found.values())
def fuzzy_candidates(name):
    found={}
    for candidate,rule,tier in candidate_variants(name):
        key=latin_key(candidate)
        if len(key)<4:
            continue
        pool=[]
        for delta in range(-MAX_EDIT_DISTANCE,MAX_EDIT_DISTANCE+1):
            pool.extend(fuzzy_buckets.get((key[0],len(key)+delta),[]))
        for pid,pname,pkey in pool:
            d=levenshtein(key,pkey,MAX_EDIT_DISTANCE)
            if d>MAX_EDIT_DISTANCE:
                continue
            sim=1.0-d/max(len(key),len(pkey))
            if sim<MIN_FUZZY_SIMILARITY:
                continue
            item=candidate_info(pid,pname,candidate,rule,tier,sim)
            old=found.get(pid)
            if old is None or (item["nameSimilarity"],-item["tier"])>(old["nameSimilarity"],-old["tier"]):
                found[pid]=item
    return list(found.values())
def classify_candidate(item,expected):
    if not expected:
        return "NO_CONTEXT",0
    if not item["latitude"] or not item["longitude"]:
        return "NO_COORDS",-1
    if not item["gisProvince"]:
        return "OUTSIDE_POLYGONS",-1
    if province_compatible(expected,item["gisProvince"],alias_targets):
        return "INSIDE_EXPECTED",2
    return "OUTSIDE_EXPECTED",-2
def rank_candidates(items,expected):
    for item in items:
        status,geo_score=classify_candidate(item,expected)
        item["provinceStatus"]=status
        item["_geoScore"]=geo_score
    items.sort(key=lambda x:(x["_geoScore"],x["nameSimilarity"],-x["tier"],not is_non_point(x["featureType"])),reverse=True)
    return items
match_rows=[]
ambiguous_rows=[]
unmatched_rows=[]
rejected_rows=[]
stats=Counter()
for occ in occurrences:
    name=occ["placeName"]
    explicit=explicit_province(name)
    expected=explicit or occ["province"]
    exact=rank_candidates(exact_candidates(name),expected)
    candidates=exact
    method="EXACT"
    if not candidates:
        candidates=rank_candidates(fuzzy_candidates(name),expected)
        method="FUZZY"
    if not candidates:
        unmatched_rows.append({**occ,"expectedProvince":expected})
        stats["unmatched"]+=1
        continue
    viable=[c for c in candidates if c["provinceStatus"]!="OUTSIDE_EXPECTED" and not is_non_point(c["featureType"])]
    chosen=None
    match_type=""
    if expected:
        inside=[c for c in viable if c["provinceStatus"]=="INSIDE_EXPECTED"]
        if len(inside)==1:
            chosen=inside[0]
            match_type="CONTEXT_EXACT" if method=="EXACT" else "CONTEXT_FUZZY"
        elif len(inside)>1 and method=="FUZZY":
            top=inside[0]
            second=inside[1]
            if top["nameSimilarity"]>=AUTO_FUZZY_SIMILARITY and top["nameSimilarity"]-second["nameSimilarity"]>=MIN_FUZZY_MARGIN:
                chosen=top
                match_type="CONTEXT_FUZZY"
        elif len(inside)>1:
            pass
        elif len(candidates)==1 and candidates[0]["provinceStatus"]=="OUTSIDE_EXPECTED":
            rejected_rows.append({**occ,"expectedProvince":expected,**{k:v for k,v in candidates[0].items() if not k.startswith("_")},"reason":"name match outside expected Notitia province"})
            stats["rejected"]+=1
            continue
    else:
        if len(viable)==1 and method=="EXACT":
            chosen=viable[0]
            match_type="EXACT_NO_CONTEXT"
        elif len(viable)==1 and method=="FUZZY" and viable[0]["nameSimilarity"]>=AUTO_FUZZY_SIMILARITY:
            chosen=viable[0]
            match_type="FUZZY_NO_CONTEXT"
    if chosen:
        match_rows.append({**occ,"expectedProvince":expected,"pleiadesId":chosen["pleiadesId"],"pleiadesName":chosen["pleiadesName"],"latitude":chosen["latitude"],"longitude":chosen["longitude"],"featureType":chosen["featureType"],"gisProvince":chosen["gisProvince"],"geojsonId":chosen["geojsonId"],"candidate":chosen["candidate"],"rule":chosen["rule"],"matchType":match_type,"similarity":f'{chosen["nameSimilarity"]:.3f}',"provinceStatus":chosen["provinceStatus"]})
        stats["matched"]+=1
        stats[match_type]+=1
        continue
    for rank,item in enumerate(candidates[:5],1):
        ambiguous_rows.append({**occ,"expectedProvince":expected,"candidateRank":rank,"pleiadesId":item["pleiadesId"],"pleiadesName":item["pleiadesName"],"latitude":item["latitude"],"longitude":item["longitude"],"featureType":item["featureType"],"gisProvince":item["gisProvince"],"geojsonId":item["geojsonId"],"candidate":item["candidate"],"rule":item["rule"],"similarity":f'{item["nameSimilarity"]:.3f}',"provinceStatus":item["provinceStatus"]})
    stats["ambiguous"]+=1
MATCH_FIELDS=["sourceNodeId","placeName","province","region","text","expectedProvince","pleiadesId","pleiadesName","latitude","longitude","featureType","gisProvince","geojsonId","candidate","rule","matchType","similarity","provinceStatus"]
AMBIGUOUS_FIELDS=["sourceNodeId","placeName","province","region","text","expectedProvince","candidateRank","pleiadesId","pleiadesName","latitude","longitude","featureType","gisProvince","geojsonId","candidate","rule","similarity","provinceStatus"]
UNMATCHED_FIELDS=["sourceNodeId","placeName","province","region","text","expectedProvince"]
REJECTED_FIELDS=["sourceNodeId","placeName","province","region","text","expectedProvince","pleiadesId","pleiadesName","latitude","longitude","featureType","gisProvince","geojsonId","candidate","rule","tier","nameSimilarity","provinceStatus","reason"]
OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
for path,fields,rows in [(MATCH_OUTPUT,MATCH_FIELDS,match_rows),(AMBIGUOUS_OUTPUT,AMBIGUOUS_FIELDS,ambiguous_rows),(UNMATCHED_OUTPUT,UNMATCHED_FIELDS,unmatched_rows),(REJECTED_OUTPUT,REJECTED_FIELDS,rejected_rows)]:
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
print()
print("Living Notitia V3")
print("match_notitia_pleiades_local.py")
print()
print("Source                  :",SOURCE_INPUT)
print("Pleiades names          :",len(name_rows))
print("Pleiades places         :",len(place_rows))
print("Province polygons       :",len(features))
print("Place occurrences       :",len(occurrences))
print("Matched                 :",stats["matched"])
print("  CONTEXT_EXACT         :",stats["CONTEXT_EXACT"])
print("  CONTEXT_FUZZY         :",stats["CONTEXT_FUZZY"])
print("  EXACT_NO_CONTEXT      :",stats["EXACT_NO_CONTEXT"])
print("  FUZZY_NO_CONTEXT      :",stats["FUZZY_NO_CONTEXT"])
print("Ambiguous               :",stats["ambiguous"])
print("Unmatched               :",stats["unmatched"])
print("Rejected by geography   :",stats["rejected"])
print()
print("Match output             :",MATCH_OUTPUT)
print("Ambiguous output         :",AMBIGUOUS_OUTPUT)
print("Unmatched output         :",UNMATCHED_OUTPUT)
print("Rejected output          :",REJECTED_OUTPUT)
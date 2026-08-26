#
# Living Notitia V3
# match_notitia_pleiades_xml_v12.py
#
from pathlib import Path
import csv
import json
import math
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict,Counter
HERE=Path(__file__).resolve()
def find_root():
    for p in [HERE.parent,*HERE.parents]:
        if (p/"data"/"notitia.xml").exists() and (p/"csv"/"PleiadesName.csv").exists():
            return p
    raise FileNotFoundError("Kan inte hitta projektroten med data/notitia.xml och csv/PleiadesName.csv")
ROOT=find_root()
XML_INPUT=ROOT/"data"/"notitia.xml"
PLACEMENTION_INPUT=ROOT/"data"/"work"/"PlaceMention.csv"
if not PLACEMENTION_INPUT.exists():
    raise FileNotFoundError(f"Kan inte hitta {PLACEMENTION_INPUT}. Kör audit_place_mentions.py först.")
PLEIADES_NAME_INPUT=ROOT/"csv"/"PleiadesName.csv"
PLEIADES_PLACE_INPUT=ROOT/"csv"/"PleiadesPlace.csv"
GEOJSON_CANDIDATES=[
    ROOT/"data"/"geojson_prov"/"provinces.geojson",
    ROOT/"geojson_prov"/"provinces.geojson",
    ROOT/"data"/"provinces.geojson"
]
GEOJSON_INPUT=next((p for p in GEOJSON_CANDIDATES if p.exists()),None)
if GEOJSON_INPUT is None:
    raise FileNotFoundError("Kan inte hitta provinces.geojson")
OUTPUT_DIR=ROOT/"csv"
MATCH_OUTPUT=OUTPUT_DIR/"PlaceMatch_context.csv"
AMBIGUOUS_OUTPUT=OUTPUT_DIR/"PlaceAmbiguous_context.csv"
UNMATCHED_OUTPUT=OUTPUT_DIR/"PlaceUnmatched_context.csv"
REJECTED_OUTPUT=OUTPUT_DIR/"PlaceRejected_context.csv"
CONFLICT_OUTPUT=OUTPUT_DIR/"PlaceConflict_context.csv"
OCCURRENCE_OUTPUT=OUTPUT_DIR/"PlaceOccurrence_context.csv"
MAX_EDIT_DISTANCE=2
MIN_FUZZY_SIMILARITY=0.86
AUTO_FUZZY_SIMILARITY=0.90
MIN_FUZZY_MARGIN=0.06
CONTEXT_THRESHOLD=0.82
NEAR_PROVINCE_KM=15.0
STOPWORDS={
    "dux","comes","comitis","vicarius","praeses","praesidis","consularis","corrector",
    "proconsul","magister","praefectus","praefecti","praepositus","vir","viri","viro",
    "spectabilis","spectabili","illustris","clarissimus","clarissimi","perfectissimus",
    "sub","dispositione","iurisdictione","per","in","intra","provincia","provinciae",
    "item","et","cum","rei","militaris","officium","habet","idem","autem","hoc","modo"
}
def clean(text):
    text=str(text or "")
    text=unicodedata.normalize("NFKD",text)
    text="".join(ch for ch in text if not unicodedata.combining(ch))
    text=text.replace("æ","ae").replace("Æ","Ae")
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
def word_forms(word):
    raw=norm(word)
    if not raw:
        return set()
    forms={latin_key(raw)}
    variants=[raw]
    if raw.endswith("iae") and len(raw)>4:
        variants.append(raw[:-3]+"ia")
    if raw.endswith("ae") and len(raw)>3:
        variants.append(raw[:-1])
    if raw.endswith("iarum") and len(raw)>6:
        variants.append(raw[:-3])
    if raw.endswith("arum") and len(raw)>5:
        variants.append(raw[:-3])
    if raw.endswith("am") and len(raw)>3:
        variants.append(raw[:-1])
    if raw.endswith("as") and len(raw)>3:
        variants.append(raw[:-1])
    if raw.endswith("is") and len(raw)>4:
        variants.append(raw[:-2]+"e")
        variants.append(raw[:-2])
    if raw.endswith("o") and len(raw)>3:
        variants.append(raw[:-1]+"um")
        variants.append(raw[:-1]+"us")
    if raw.endswith("i") and len(raw)>3:
        variants.append(raw[:-1]+"us")
        variants.append(raw[:-1]+"um")
    for value in variants:
        key=latin_key(value)
        if key:
            forms.add(key)
    return forms
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
def string_similarity(a,b):
    a=latin_key(a)
    b=latin_key(b)
    if not a or not b:
        return 0.0
    d=levenshtein(a,b)
    return 1.0-d/max(len(a),len(b))
def word_similarity(a,b):
    best=0.0
    for fa in word_forms(a):
        for fb in word_forms(b):
            if fa==fb:
                return 1.0
            d=levenshtein(fa,fb)
            score=1.0-d/max(len(fa),len(fb))
            best=max(best,score)
    return best
def meaningful_tokens(text):
    result=[]
    for token in norm(text).split():
        if token in STOPWORDS or len(token)<3:
            continue
        result.append(token)
    return result
def expected_to_actual_score(expected,actual):
    expected_tokens=meaningful_tokens(expected)
    actual_tokens=meaningful_tokens(actual)
    if not expected_tokens or not actual_tokens:
        return 0.0
    scores=[]
    for e in expected_tokens:
        scores.append(max(word_similarity(e,a) for a in actual_tokens))
    return sum(scores)/len(scores)
def actual_to_context_score(actual,context):
    actual_tokens=meaningful_tokens(actual)
    context_tokens=meaningful_tokens(context)
    if not actual_tokens or not context_tokens:
        return 0.0
    scores=[]
    for a in actual_tokens:
        scores.append(max(word_similarity(a,c) for c in context_tokens))
    scores.sort(reverse=True)
    if len(scores)==1:
        return scores[0]
    return 0.65*scores[0]+0.35*scores[1]
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
def get_number_text(row,*names):
    for name in names:
        value=str(row.get(name,"") or "").strip()
        if value:
            return value
    return ""
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
def toponymic_variants(text):
    text=clean(text)
    if not text or len(text.split())!=1:
        return []
    word=text
    lower=word.lower()
    result=[]
    seen=set()
    def add(value,rule):
        value=clean(value)
        key=norm(value)
        if value and key and key!=norm(text) and key not in seen:
            seen.add(key)
            result.append((value,rule))
    patterns=[
        ("itanorum",["a","um","us","o","is","e","ia"]),
        ("ianorum",["ia","a","um","us","o","is","e"]),
        ("iensium",["ia","a","um","us","o","is","e","i"]),
        ("ensium",["um","a","ia","e","is","us","o","i"]),
        ("iensis",["ia","a","um","us","o","is","e"]),
        ("ensis",["um","a","ia","e","is","us","o","i"]),
        ("atis",["a","um","us","e","is","o","i"]),
        ("orum",["i","um","a","ia","us","o","e"])
    ]
    for suffix,endings in patterns:
        if lower.endswith(suffix) and len(word)>len(suffix)+2:
            stem=word[:-len(suffix)]
            add(stem,"toponymic_"+suffix+"_stem")
            for ending in endings:
                add(stem+ending,"toponymic_"+suffix)
            break
    return result
def candidate_variants(place_name,place_source=""):
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
    if place_source=="limes":
        add("Limes "+place_name,"limes_title",0)
    aliases={
        "maccomadensis":["Macomades"],
        "girbitani":["Girba"],
        "girbitanus":["Girba"],
        "syracusani":["Syracusae"],
        "tarentini":["Tarentum"],
        "dubris":["Portus Dubris"]
    }
    for alias in aliases.get(norm(place_name),[]):
        add(alias,"toponymic_alias",0)
    m=re.search(r"\bin\s+castello\s+(.+)$",place_name,flags=re.I)
    if m:
        add(m.group(1),"in_castello",0)
    m=re.search(r"\bin\s+castris\s+(.+)$",place_name,flags=re.I)
    if m:
        add("Castra "+m.group(1),"in_castris",0)
        add(m.group(1),"in_castris_name",1)
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
        for topo_value,topo_rule in toponymic_variants(value):
            add(topo_value,topo_rule,tier+1)
    for value,rule,tier in list(result):
        words=value.split()
        if len(words)>1:
            add(words[0],"first_word",1)
            for case_value in case_variants(words[0]):
                if norm(case_value)!=norm(words[0]):
                    add(case_value,"first_word_case",1)
            for topo_value,topo_rule in toponymic_variants(words[0]):
                add(topo_value,"first_word_"+topo_rule,2)
    return result
def hard_province_from_title(title,group_type=""):
    title=clean(title)
    if not title:
        return ""
    patterns=[
        r"^(?:item\s+)?in\s+provincia\s+(.+)$",
        r"^provincia\s+(.+)$",
        r"^provinciae\s+(.+)$"
    ]
    for pattern in patterns:
        m=re.search(pattern,title,flags=re.I)
        if m:
            return clean(m.group(1))
    if "province" in norm(group_type) and len(title.split())<=6:
        return clean(re.sub(r"^(?:item\s+)?in\s+provincia\s+","",title,flags=re.I))
    m=re.match(r"^in\s+(.+)$",title,flags=re.I)
    if m:
        value=clean(m.group(1))
        if not re.search(r"\b(?:castello|castris|barbarico|litore|lineam)\b",value,flags=re.I):
            return value
    return ""
def soft_province_from_title(title):
    title=clean(title)
    if not title:
        return ""
    patterns=[
        r"\bducis\s+provinciae\s+(.+)$",
        r"\bducis\s+(.+)$",
        r"^dux\s+provinciae\s+(.+)$",
        r"^dux\s+(.+)$",
        r"^praeses\s+(.+)$",
        r"^consularis\s+(.+)$",
        r"^corrector\s+(.+)$",
        r"^comes\s+limitis\s+(.+)$"
    ]
    for pattern in patterns:
        m=re.search(pattern,title,flags=re.I)
        if m:
            return clean(m.group(1))
    return ""
def region_from_title(title,group_type=""):
    title=clean(title)
    if not title:
        return ""
    key=norm(title)
    known_patterns=[
        (r"^(?:per|in)\s+illyric", "ILLYRICUM"),
        (r"^(?:per|in)\s+itali", "ITALIA"),
        (r"^italiae?$", "ITALIA"),
        (r"^(?:per|in)\s+galli", "GALLIAE"),
        (r"^gallicanarum$", "GALLIAE"),
        (r"^in\s+britanni", "BRITANNIA"),
        (r"^britannia", "BRITANNIA"),
        (r"^orientis(?:\s+\w+)?$", "ORIENS"),
        (r"^orientalium$", "ORIENS"),
        (r"^ponticae(?:\s+\w+)?$", "PONTICA"),
        (r"^asianae(?:\s+\w+)?$", "ASIANA"),
        (r"^thraciarum(?:\s+\w+)?$", "THRACIAE"),
        (r"^africae?$", "AFRICA"),
        (r"^hispaniae?$", "HISPANIA")
    ]
    for pattern,value in known_patterns:
        if re.search(pattern,key):
            return value
    if "region" in norm(group_type):
        return title
    if re.match(r"^intra\s+",title,flags=re.I):
        return title
    return ""
def explicit_province(place_name):
    text=clean(place_name)
    m=re.search(r"\bin\s+(.+)$",text)
    if not m:
        return ""
    suffix=clean(m.group(1))
    if not suffix or not suffix[0].isupper():
        return ""
    if re.search(r"\b(?:castello|castris|barbarico)\b",suffix,flags=re.I):
        return ""
    return suffix
placemention_rows=load_csv(PLACEMENTION_INPUT)
eligible_mentions={}
placeholder_mentions=0
for row in placemention_rows:
    if clean(row.get("pointEligible",""))!="1":
        continue
    literal=clean(row.get("literalForm",""))
    if not literal:
        placeholder_mentions+=1
        continue
    key=(clean(row.get("document","")),clean(row.get("line","")),literal,clean(row.get("source","")))
    if key in eligible_mentions:
        raise ValueError(f"Duplicate eligible PlaceMention key: {key}")
    eligible_mentions[key]=row
used_mentions=set()
tree=ET.parse(XML_INPUT)
root=tree.getroot()
occurrences=[]
counter=1
documents=root.findall(".//document")
if root.tag=="document":
    documents=[root]
if not documents:
    documents=[root]
def title_of(element):
    node=element.find("title")
    return clean(node.text) if node is not None and node.text else ""
def walk(element,document_name,chapter_title,hard_province,soft_province,region,titles):
    global counter
    local_hard=hard_province
    local_soft=soft_province
    local_region=region
    local_titles=list(titles)
    if element.tag=="group":
        group_title=title_of(element)
        group_type=element.get("type","")
        if group_title:
            local_titles.append(group_title)
        detected_hard=hard_province_from_title(group_title,group_type)
        detected_soft=soft_province_from_title(group_title)
        detected_region=region_from_title(group_title,group_type)
        if detected_hard:
            local_hard=detected_hard
        if detected_soft:
            local_soft=detected_soft
        if detected_region:
            local_region=detected_region
    direct_unit=""
    direct_office=""
    direct_province=""
    direct_region=""
    for child in element:
        if child.tag=="unit" and child.text and not direct_unit:
            direct_unit=clean(child.text)
        if child.tag=="office" and child.text and not direct_office:
            direct_office=clean(child.text)
        if child.tag=="province" and child.text and not direct_province:
            direct_province=clean(child.text)
        if child.tag=="region" and child.text and not direct_region:
            direct_region=clean(child.text)
    occurrence_region=local_region
    if direct_region:
        occurrence_region=region_from_title(direct_region,"region") or direct_region
    for child in element:
        if child.tag!="place" or not child.text:
            continue
        place_name=clean(child.text)
        if not place_name:
            continue
        place_source=clean(child.get("source",""))
        mention_key=(document_name,clean(element.get("line","")),place_name,place_source)
        mention=eligible_mentions.get(mention_key)
        if mention is None:
            continue
        used_mentions.add(mention_key)
        explicit=explicit_province(place_name)
        hard=explicit or direct_province or local_hard
        soft=local_soft
        expected=hard or soft
        occurrences.append({
            "occurrenceId":f"OCC{counter:06d}",
            "document":document_name,
            "chapter":chapter_title,
            "sourceLine":clean(element.get("line","")),
            "placeName":place_name,
            "placeSource":place_source,
            "office":direct_office,
            "unit":direct_unit,
            "declaredProvince":direct_province or local_hard or local_soft,
            "explicitProvince":explicit,
            "hardProvince":hard,
            "softProvince":soft,
            "expectedProvince":expected,
            "region":occurrence_region,
            "contextText":" / ".join([chapter_title,*local_titles])
        })
        counter+=1
    for child in element:
        if child.tag in {"title","place","unit","office","function"}:
            continue
        walk(child,document_name,chapter_title,local_hard,local_soft,local_region,local_titles)
for document in documents:
    document_name=clean(document.get("id","") or document.get("name","") or document.tag)
    chapters=document.findall("chapter")
    if not chapters and document is root:
        chapters=root.findall(".//chapter")
    for chapter in chapters:
        chapter_title=title_of(chapter)
        chapter_soft=soft_province_from_title(chapter_title)
        walk(chapter,document_name,chapter_title,"",chapter_soft,"",[chapter_title] if chapter_title else [])
missing_mentions=[key for key in eligible_mentions if key not in used_mentions]
if missing_mentions:
    sample="; ".join(" / ".join(key) for key in missing_mentions[:10])
    raise ValueError(f"{len(missing_mentions)} eligible PlaceMention rows saknar motsvarande place i notitia.xml: {sample}")
name_rows=load_csv(PLEIADES_NAME_INPUT)
place_rows=load_csv(PLEIADES_PLACE_INPUT)
with GEOJSON_INPUT.open(encoding="utf-8") as f:
    geojson=json.load(f)
features=[f for f in geojson.get("features",[]) if f.get("geometry",{}).get("type") in {"Polygon","MultiPolygon"}]
def feature_name(feature):
    p=feature.get("properties",{})
    return clean(p.get("PROV_NAME") or p.get("prov_name") or p.get("NAME") or p.get("name") or p.get("PROVINCE") or p.get("province"))
def feature_id(feature):
    p=feature.get("properties",{})
    return clean(p.get("geojsonId") or p.get("GEOJSONID") or p.get("id") or feature.get("id",""))
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
province_cache={}
def containing_province(latitude,longitude):
    lat=to_float(latitude)
    lon=to_float(longitude)
    if lat is None or lon is None:
        return "",""
    key=(lat,lon)
    if key in province_cache:
        return province_cache[key]
    for feature in features:
        if point_in_geometry(lon,lat,feature.get("geometry")):
            result=(feature_name(feature),feature_id(feature))
            province_cache[key]=result
            return result
    province_cache[key]=("","")
    return "",""
nearest_cache={}
def geometry_rings(geometry):
    if not geometry:
        return []
    kind=geometry.get("type","")
    coords=geometry.get("coordinates",[])
    if kind=="Polygon":
        return coords
    if kind=="MultiPolygon":
        return [ring for polygon in coords for ring in polygon]
    return []
def point_segment_distance_km(lon,lat,lon1,lat1,lon2,lat2):
    scale_x=111.32*math.cos(math.radians(lat))
    scale_y=110.57
    px=lon*scale_x
    py=lat*scale_y
    x1=lon1*scale_x
    y1=lat1*scale_y
    x2=lon2*scale_x
    y2=lat2*scale_y
    dx=x2-x1
    dy=y2-y1
    if dx==0 and dy==0:
        return math.hypot(px-x1,py-y1)
    t=((px-x1)*dx+(py-y1)*dy)/(dx*dx+dy*dy)
    t=max(0.0,min(1.0,t))
    x=x1+t*dx
    y=y1+t*dy
    return math.hypot(px-x,py-y)
def nearest_province(latitude,longitude):
    lat=to_float(latitude)
    lon=to_float(longitude)
    if lat is None or lon is None:
        return "","",None
    key=(lat,lon)
    if key in nearest_cache:
        return nearest_cache[key]
    best_name=""
    best_id=""
    best_distance=None
    for feature in features:
        for ring in geometry_rings(feature.get("geometry")):
            if len(ring)<2:
                continue
            for i in range(1,len(ring)):
                distance=point_segment_distance_km(
                    lon,lat,
                    ring[i-1][0],ring[i-1][1],
                    ring[i][0],ring[i][1]
                )
                if best_distance is None or distance<best_distance:
                    best_distance=distance
                    best_name=feature_name(feature)
                    best_id=feature_id(feature)
    result=(best_name,best_id,best_distance)
    nearest_cache[key]=result
    return result
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
polygon_names=[feature_name(f) for f in features if feature_name(f)]
def chapter_has_geography(chapter_title):
    if not chapter_title:
        return False
    return max((actual_to_context_score(name,chapter_title) for name in polygon_names),default=0.0)>=CONTEXT_THRESHOLD
def candidate_info(pid,pname,candidate,rule,tier,name_similarity):
    place=place_by_id.get(pid,{})
    lat=get_number_text(place,"latitude","lat")
    lon=get_number_text(place,"longitude","lon","lng")
    feature_type=get(place,"featureType","type")
    gis_province,geojson_id=containing_province(lat,lon)
    nearest_name=""
    nearest_id=""
    nearest_km=None
    if not gis_province:
        nearest_name,nearest_id,nearest_km=nearest_province(lat,lon)
    return {
        "pleiadesId":pid,
        "pleiadesName":pname,
        "candidate":candidate,
        "rule":rule,
        "tier":tier,
        "nameSimilarity":name_similarity,
        "latitude":lat,
        "longitude":lon,
        "featureType":feature_type,
        "gisProvince":gis_province,
        "geojsonId":geojson_id,
        "nearestProvince":nearest_name,
        "nearestGeojsonId":nearest_id,
        "nearestKm":"" if nearest_km is None else f"{nearest_km:.2f}"
    }
LIMES_ANCHORS={
    "bazensis":("334577","Limes Bazensis"),
    "gemellensis":("334578","Limes Gemellensis"),
    "montensis":("334579","Limes Montensis"),
    "tubuniensis":("334580","Limes Tubunensis"),
    "caputcellensis":("299007","Limes Caputcellensis")
}
TOPONYMIC_ANCHORS={
    "lugdunensium":("167717","Col. Lugdunum"),
    "lugdunensis":("167717","Col. Lugdunum"),
    "arelatensium":("148217","Col. Arelate"),
    "arelatensis":("148217","Col. Arelate"),
    "remorum":("108945","Durocortorum"),
    "remensis":("108945","Durocortorum"),
    "triberorum":("108894","Col. Augusta Treverorum"),
    "mediolanensium":("383706","Mediolanum"),
    "mediolanensis":("383706","Mediolanum"),
    "aquileiensium":("187290","Aquileia"),
    "aquileiensis":("187290","Aquileia"),
    "siscianorum":("197504","Siscia"),
    "siscianae":("197504","Siscia"),
    "salonitanorum":("197488","Salona"),
    "salonitani":("197488","Salona"),
    "sabariensium":("197498","Savaria"),
    "talalatensis":("344498","Talalati"),
    "tillibarensis":("344516","Tillibari"),
    "leptitanis":("344448","Lepcitani"),
    "lepcitani":("344448","Lepcitani"),
    "tungros":("108765","Atuatuca Tungrorum"),
    "tungrorum":("108765","Atuatuca Tungrorum"),
    "carthagiensis":("314921","Carthago")
}
def anchored_candidates(name,place_source=""):
    if place_source=="limes":
        anchor=LIMES_ANCHORS.get(norm(name))
        if anchor:
            pid,pname=anchor
            return [candidate_info(pid,pname,name,"limes_anchor",0,1.0)]
    anchor=TOPONYMIC_ANCHORS.get(norm(name))
    if not anchor:
        return []
    pid,pname=anchor
    return [candidate_info(pid,pname,name,"toponymic_anchor",0,1.0)]
def exact_candidates(name,place_source=""):
    found={}
    for candidate,rule,tier in candidate_variants(name,place_source):
        for pid,pname in exact_index.get(norm(candidate),{}).items():
            item=candidate_info(pid,pname,candidate,rule,tier,1.0)
            old=found.get(pid)
            if old is None or (item["tier"],len(item["candidate"]))<(old["tier"],len(old["candidate"])):
                found[pid]=item
    return list(found.values())
def fuzzy_candidates(name,place_source=""):
    found={}
    for candidate,rule,tier in candidate_variants(name,place_source):
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
PROVINCE_TARGET_ALIASES={
    "achaiae":["ACHAIA"],
    "aemiliae":["AEMILIA ET LIGURIA"],
    "aemilia":["AEMILIA ET LIGURIA"],
    "liguriae":["AEMILIA ET LIGURIA"],
    "alpium cottiarum":["ALPES COTTIAE"],
    "alpium poeninarum et graiarum":["ALPES GRAIAE ET POENINAE"],
    "alpium maritimarum":["ALPES MARITIMAE"],
    "apuliae et calabriae":["APULIA ET CALABRIA"],
    "aquitanicae primae":["AQUITANIA I"],
    "aquitanicae secundae":["AQUITANIA II"],
    "arabiae":["ARABIA"],
    "asiae":["ASIA"],
    "augusta eufratensi":["AUGUSTA EUPHRATENSIS"],
    "augusta euphratensi":["AUGUSTA EUPHRATENSIS"],
    "baeticae":["BAETICA"],
    "belgicae primae":["BELGICA I"],
    "belgicae secundae":["BELGICA II"],
    "balgicae secundae":["BELGICA II"],
    "bithyniae":["BITHYNIA"],
    "britanniae":["BRITANNIAE I AND II"],
    "britanniarum":["BRITANNIAE I AND II"],
    "byzacii":["BYZACENA"],
    "campaniae":["CAMPANIA"],
    "cappadociae primae":["CAPPADOCIA"],
    "cappadociae secundae":["CAPPADOCIA"],
    "cariae":["CARIA"],
    "callaeciae":["GALLAECIA"],
    "callaecia":["GALLAECIA"],
    "ciliciae":["CILICIA"],
    "corsicae":["CORSICA"],
    "cretae":["CRETA"],
    "cypri":["CYPRUS"],
    "daciae mediterraneae":["DACIA MEDITERRANEA"],
    "daciae ripensis":["DACIA RIPENSIS"],
    "dalmaticarum":["DALMATIA"],
    "dardaniae":["DARDANIA"],
    "epiri nouae":["EPIRUS NOVA"],
    "epiri ueteris":["EPIRUS VETUS"],
    "europae":["EUROPA"],
    "flaminiae et piceni annonarii":["FLAMINIA ET PICENUM"],
    "flaminia":["FLAMINIA ET PICENUM"],
    "galatiae":["GALATIA"],
    "germaniae primae":["GERMANIA I"],
    "germaniae secundae":["GERMANIA II"],
    "haemimonti":["HAEMIMONTUS"],
    "hellesponti":["HELLESPONTUS"],
    "insularum":["INSULAE"],
    "libyae inferioris":["LIBYA INFERIOR"],
    "libyae superioris":["LIBYA SUPERIOR"],
    "lucaniae et brittiorum":["LUCANIA ET BRUTTII"],
    "lugdunensis primae":["LUGDUNENSIS I"],
    "lugdunensis secundae":["LUGDUNENSIS II"],
    "lusitaniae":["LUSITANIA"],
    "lyciae":["LYCIA ET PAMPHYLIA"],
    "pamfyliae":["LYCIA ET PAMPHYLIA"],
    "lydiae":["LYDIA"],
    "macedoniae":["MACEDONIA"],
    "mauretaniae sitifensis":["MAURETANIA SITIFENSIS"],
    "tingitaniae":["MAURETANIA TINGITANA"],
    "mesopotamiae":["MESOPOTAMIA"],
    "narbonensis primae":["NARBONENSIS I"],
    "narbonensis secundae":["NARBONENSIS II"],
    "norici mediterranei":["NORICUM MEDITERRANEUM"],
    "norici ripensis":["NORICUM RIPENSE"],
    "novempopulanae":["NOVEM POPULI"],
    "osroehenae":["OSRHOENE"],
    "osrhoenae":["OSRHOENE"],
    "palaestinae":["PALAESTINA"],
    "paflagoniae":["PAPHLAGONIA"],
    "pisidiae":["PISIDIA"],
    "ponti polemoniaci":["PONTUS POLEMONIACUS"],
    "praeualitanae":["PRAEVALITANA"],
    "rhodopae":["RHODOPE"],
    "saradiniae":["SARDINIA"],
    "saviae":["SAVIA"],
    "scythiae":["SCYTHIA"],
    "maximae sequanorum":["SEQUANIA"],
    "siciliae":["SICILIA"],
    "syriae":["SYRIA COELE"],
    "tarraconensis":["TARRACONENSIS"],
    "thebaidos":["THEBAIS"],
    "thessaliae":["THESSALIA"],
    "thraciae":["THRACIA"],
    "tripolitanae":["TRIPOLITANA"],
    "tusciae et umbriae":["TUSCIA ET UMBRIA"],
    "valeriae":["VALERIA"],
    "valeriae ripensis":["VALERIA"],
    "venetiae et histriae":["VENETIA ET HISTRIA"],
    "viennensis":["VIENNENSIS"],
    "pannoniae":["PANNONIA INFERIOR","PANNONIA SUPERIOR"],
    "pannoniae primae":["PANNONIA SUPERIOR"],
    "pannoniae secundae":["PANNONIA INFERIOR"],
    "pannoniae secundae ripariensis":["PANNONIA INFERIOR"],
    "moesiae primae":["MOESIA SUPERIOR"],
    "moesiae secundae":["MOESIA INFERIOR"],
    "raetiae":["RAETIA"],
    "raetiae primae":["RAETIA"],
    "raetiae secundae":["RAETIA"],
    "raetiae primae et secundae":["RAETIA"],
    "aegypti":["AEGYPTUS HERCULIA","AEGYPTUS IOVIA"],
    "foenicis":["PHOENICE","AUGUSTA LIBANENSIS"],
    "armeniae":["ARMENIA MINOR"],
    "mogontiacensis":["GERMANIA I"]
}
def province_targets(expected):
    expected=clean(expected)
    if not expected:
        return []
    key=norm(expected)
    targets=[]
    def add(names):
        for name in names:
            if name in polygon_names and name not in targets:
                targets.append(name)
    if key in PROVINCE_TARGET_ALIASES:
        add(PROVINCE_TARGET_ALIASES[key])
    parts=[clean(x) for x in re.split(r"\bet\b",expected,flags=re.I) if clean(x)]
    for part in parts:
        pkey=norm(part)
        if pkey in PROVINCE_TARGET_ALIASES:
            add(PROVINCE_TARGET_ALIASES[pkey])
    for name in polygon_names:
        if expected_to_actual_score(expected,name)>=CONTEXT_THRESHOLD:
            add([name])
    for part in parts:
        for name in polygon_names:
            if expected_to_actual_score(part,name)>=CONTEXT_THRESHOLD:
                add([name])
    return targets
def province_supported(expected):
    return bool(province_targets(expected))
REGION_TARGETS={
    "ITALIA":{"AEMILIA ET LIGURIA","APULIA ET CALABRIA","CAMPANIA","FLAMINIA ET PICENUM","LUCANIA ET BRUTTII","TUSCIA ET UMBRIA","VENETIA ET HISTRIA","SICILIA","SARDINIA","CORSICA"},
    "GALLIAE":{"AQUITANIA I","AQUITANIA II","BELGICA I","BELGICA II","GERMANIA I","GERMANIA II","LUGDUNENSIS I","LUGDUNENSIS II","NARBONENSIS I","NARBONENSIS II","NOVEM POPULI","SEQUANIA","VIENNENSIS","ALPES COTTIAE","ALPES GRAIAE ET POENINAE","ALPES MARITIMAE"},
    "BRITANNIA":{"BRITANNIAE I AND II"},
    "ILLYRICUM":{"PANNONIA INFERIOR","PANNONIA SUPERIOR","SAVIA","NORICUM MEDITERRANEUM","NORICUM RIPENSE","DALMATIA","PRAEVALITANA","DARDANIA","DACIA MEDITERRANEA","DACIA RIPENSIS","MACEDONIA","ACHAIA","EPIRUS NOVA","EPIRUS VETUS","THESSALIA"},
    "ORIENS":{"SYRIA COELE","PHOENICE","AUGUSTA LIBANENSIS","PALAESTINA","ARABIA","CILICIA","CYPRUS","OSRHOENE","MESOPOTAMIA","AUGUSTA EUPHRATENSIS"},
    "PONTICA":{"BITHYNIA","PAPHLAGONIA","GALATIA","CAPPADOCIA","ARMENIA MINOR","PONTUS POLEMONIACUS","DIOSPONTUS"},
    "ASIANA":{"ASIA","LYDIA","CARIA","PHRYGIA I","PHRYGIA II","LYCIA ET PAMPHYLIA","PISIDIA","HELLESPONTUS","INSULAE"},
    "THRACIAE":{"EUROPA","THRACIA","HAEMIMONTUS","RHODOPE","MOESIA INFERIOR","SCYTHIA"},
    "AFRICA":{"AFRICA PROCONSULARIS","BYZACENA","NUMIDIA CIRTENSIS","NUMIDIA MILITIANA","MAURETANIA CAESARIENSIS","MAURETANIA SITIFENSIS","TRIPOLITANA"},
    "HISPANIA":{"BAETICA","LUSITANIA","TARRACONENSIS","GALLAECIA","CARTBAGINIENSIS"}
}
def region_targets(region):
    key=clean(region).upper()
    if key in REGION_TARGETS:
        return REGION_TARGETS[key]
    detected=region_from_title(region)
    return REGION_TARGETS.get(detected,set())
def military_occurrence(occ):
    chapter=norm(occ.get("chapter",""))
    return bool(clean(occ.get("unit",""))) or chapter.startswith("dux ") or chapter.startswith("comes limitis ") or chapter.startswith("comes britann") or chapter.startswith("comes tractus ")
def feature_score(occ,item):
    f=norm(item.get("featureType",""))
    if not f:
        return 0
    military_words=("fort","fortlet","camp","military","watchtower","watch tower","tower","fortification","castr")
    site_words=("settlement","major settlement","city","town","village","vicus","station","port","harbor","harbour")
    nonsite_words=("river","stream","road","route","region","province","mountain","hill","people","tribe","island","sea","lake","bay","cape")
    if military_occurrence(occ) and any(w in f for w in military_words):
        return 4
    if any(w in f for w in site_words):
        return 2
    if any(w in f for w in nonsite_words):
        return -2
    return 0
def choose_by_feature(occ,candidates,method):
    if len(candidates)<2:
        return None,""
    scored=sorted(((feature_score(occ,c),c) for c in candidates),key=lambda x:(x[0],x[1]["nameSimilarity"],-x[1]["tier"]),reverse=True)
    top_score,top=scored[0]
    second_score=scored[1][0]
    unique_top=sum(1 for score,_ in scored if score==top_score)==1
    safe=(top_score>=4 and top_score-second_score>=2) or (top_score>=2 and second_score<0)
    if not unique_top or not safe:
        return None,""
    if method=="FUZZY" and top["nameSimilarity"]<AUTO_FUZZY_SIMILARITY:
        return None,""
    return top,("FEATURE_EXACT" if method=="EXACT" else "FEATURE_FUZZY")
def score_context(occ,item):
    actual=item["gisProvince"]
    nearest=item.get("nearestProvince","")
    try:
        nearest_km=float(item.get("nearestKm",""))
    except (TypeError,ValueError):
        nearest_km=None
    hard=occ.get("hardProvince","")
    soft=occ.get("softProvince","")
    region=occ.get("region","")
    hard_targets=province_targets(hard)
    soft_targets=province_targets(soft)
    macro_targets=region_targets(region)
    if hard_targets:
        if actual:
            if actual in hard_targets:
                return "HARD_MATCH",1.0,"HARD"
            return "HARD_MISMATCH",expected_to_actual_score(hard,actual),"HARD"
        if nearest and nearest_km is not None and nearest_km<=NEAR_PROVINCE_KM:
            if nearest in hard_targets:
                return "HARD_NEAR_MATCH",1.0,"HARD"
            return "HARD_NEAR_MISMATCH",expected_to_actual_score(hard,nearest),"HARD"
        return "HARD_UNVERIFIED",0.0,"HARD"
    if soft_targets:
        if actual:
            if actual in soft_targets:
                return "SOFT_MATCH",1.0,"SOFT"
            return "SOFT_MISMATCH",expected_to_actual_score(soft,actual),"SOFT"
        if nearest and nearest_km is not None and nearest_km<=NEAR_PROVINCE_KM:
            if nearest in soft_targets:
                return "SOFT_NEAR_MATCH",1.0,"SOFT"
            return "SOFT_NEAR_MISMATCH",expected_to_actual_score(soft,nearest),"SOFT"
        return "SOFT_UNVERIFIED",0.0,"SOFT"
    if macro_targets:
        if actual:
            return ("REGION_MATCH" if actual in macro_targets else "REGION_MISMATCH"),(1.0 if actual in macro_targets else 0.0),"REGION"
        if nearest and nearest_km is not None and nearest_km<=NEAR_PROVINCE_KM:
            return ("REGION_NEAR_MATCH" if nearest in macro_targets else "REGION_NEAR_MISMATCH"),(1.0 if nearest in macro_targets else 0.0),"REGION"
        return "REGION_UNVERIFIED",0.0,"REGION"
    if actual and chapter_has_geography(occ["chapter"]):
        score=actual_to_context_score(actual,occ["contextText"])
        return ("SOFT_MATCH" if score>=CONTEXT_THRESHOLD else "SOFT_MISMATCH"),score,"SOFT"
    if nearest and nearest_km is not None and nearest_km<=NEAR_PROVINCE_KM and chapter_has_geography(occ["chapter"]):
        score=actual_to_context_score(nearest,occ["contextText"])
        return ("SOFT_NEAR_MATCH" if score>=CONTEXT_THRESHOLD else "SOFT_NEAR_MISMATCH"),score,"SOFT"
    return ("NO_POLYGON" if not actual else "NO_CONTEXT"),0.0,"NONE"
def rank_candidates(occ,items):
    priority={"HARD_MATCH":7,"HARD_NEAR_MATCH":6,"SOFT_MATCH":5,"SOFT_NEAR_MATCH":4,"REGION_MATCH":3,"REGION_NEAR_MATCH":2}
    for item in items:
        status,context_score,strength=score_context(occ,item)
        item["contextStatus"]=status
        item["contextScore"]=context_score
        item["contextStrength"]=strength
    items.sort(key=lambda x:(priority.get(x["contextStatus"],0),x["contextScore"],x["nameSimilarity"],feature_score(occ,x),-x["tier"]),reverse=True)
    return items
match_rows=[]
ambiguous_rows=[]
unmatched_rows=[]
rejected_rows=[]
conflict_rows=[]
stats=Counter()
for occ in occurrences:
    candidates=rank_candidates(occ,anchored_candidates(occ["placeName"],occ.get("placeSource","")))
    method="EXACT"
    if candidates:
        stats["anchor_occurrences"]+=1
    if not candidates:
        candidates=rank_candidates(occ,exact_candidates(occ["placeName"],occ.get("placeSource","")))
        method="EXACT"
    if not candidates:
        candidates=rank_candidates(occ,fuzzy_candidates(occ["placeName"],occ.get("placeSource","")))
        method="FUZZY"
    if not candidates:
        unmatched_rows.append(occ.copy())
        stats["unmatched"]+=1
        continue
    hard_present=bool(occ.get("hardProvince")) and province_supported(occ.get("hardProvince",""))
    hard_direct=[c for c in candidates if c["contextStatus"]=="HARD_MATCH"]
    hard_near=[c for c in candidates if c["contextStatus"]=="HARD_NEAR_MATCH"]
    hard_matching=hard_direct+hard_near
    hard_mismatch=[c for c in candidates if c["contextStatus"] in {"HARD_MISMATCH","HARD_NEAR_MISMATCH"}]
    hard_unverified=[c for c in candidates if c["contextStatus"]=="HARD_UNVERIFIED"]
    soft_direct=[c for c in candidates if c["contextStatus"]=="SOFT_MATCH"]
    soft_near=[c for c in candidates if c["contextStatus"]=="SOFT_NEAR_MATCH"]
    soft_matching=soft_direct+soft_near
    region_direct=[c for c in candidates if c["contextStatus"]=="REGION_MATCH"]
    region_near=[c for c in candidates if c["contextStatus"]=="REGION_NEAR_MATCH"]
    region_matching=region_direct+region_near
    chosen=None
    match_type=""
    if hard_present:
        pool=hard_direct if hard_direct else hard_near
        if len(pool)==1:
            chosen=pool[0]
            is_near=chosen["contextStatus"]=="HARD_NEAR_MATCH"
            if method=="EXACT":
                match_type="CONTEXT_NEAR_EXACT" if is_near else "CONTEXT_EXACT"
            elif chosen["nameSimilarity"]>=AUTO_FUZZY_SIMILARITY:
                match_type="CONTEXT_NEAR_FUZZY" if is_near else "CONTEXT_FUZZY"
        elif len(pool)>1:
            chosen,match_type=choose_by_feature(occ,pool,method)
        if not hard_matching and hard_mismatch and not hard_unverified:
            for rank,item in enumerate(candidates[:5],1):
                conflict_rows.append({**occ,"candidateRank":rank,**{k:v for k,v in item.items() if k!="contextStrength"},"reason":"Namnmatchning finns men provinsonpolygonen motsager uttrycklig Notitia-kontext"})
            if len(candidates)==1:
                candidate=candidates[0]
                if method=="EXACT":
                    chosen=candidate
                    match_type="CONTEXT_CONFLICT_EXACT"
                elif candidate["nameSimilarity"]>=AUTO_FUZZY_SIMILARITY:
                    chosen=candidate
                    match_type="CONTEXT_CONFLICT_FUZZY"
    else:
        pool=soft_direct if soft_direct else soft_near
        if len(pool)==1:
            chosen=pool[0]
            is_near=chosen["contextStatus"]=="SOFT_NEAR_MATCH"
            if method=="EXACT":
                match_type="CONTEXT_NEAR_EXACT" if is_near else "CONTEXT_EXACT"
            elif chosen["nameSimilarity"]>=AUTO_FUZZY_SIMILARITY:
                match_type="CONTEXT_NEAR_FUZZY" if is_near else "CONTEXT_FUZZY"
        elif len(pool)>1:
            chosen,match_type=choose_by_feature(occ,pool,method)
        if chosen is None and not pool:
            rpool=region_direct if region_direct else region_near
            if len(rpool)==1:
                chosen=rpool[0]
                is_near=chosen["contextStatus"]=="REGION_NEAR_MATCH"
                if method=="EXACT":
                    match_type="REGION_NEAR_EXACT" if is_near else "REGION_EXACT"
                elif chosen["nameSimilarity"]>=AUTO_FUZZY_SIMILARITY:
                    match_type="REGION_NEAR_FUZZY" if is_near else "REGION_FUZZY"
            elif len(rpool)>1:
                chosen,match_type=choose_by_feature(occ,rpool,method)
    if chosen is None:
        compatible=hard_matching or soft_matching or region_matching
        if compatible:
            chosen,match_type=choose_by_feature(occ,compatible,method)
        else:
            chosen,match_type=choose_by_feature(occ,candidates,method)
    if chosen:
        match_rows.append({**occ,**{k:v for k,v in chosen.items() if k!="contextStrength"},"matchType":match_type,"similarity":f'{chosen["nameSimilarity"]:.3f}',"contextScore":f'{chosen["contextScore"]:.3f}'})
        stats["matched"]+=1
        stats[match_type]+=1
        if "toponymic_" in chosen.get("rule",""):
            stats["toponymic_matched"]+=1
        if chosen.get("rule")=="toponymic_anchor":
            stats["anchor_matched"]+=1
        if chosen.get("rule")=="limes_anchor":
            stats["limes_anchor_matched"]+=1
        continue
    if len(candidates)==1 and method=="EXACT":
        chosen=candidates[0]
        match_type="EXACT_NO_CONTEXT"
    elif len(candidates)==1 and method=="FUZZY" and candidates[0]["nameSimilarity"]>=AUTO_FUZZY_SIMILARITY and occ.get("placeSource","")!="limes":
        chosen=candidates[0]
        match_type="FUZZY_NO_CONTEXT"
    if chosen:
        match_rows.append({**occ,**{k:v for k,v in chosen.items() if k!="contextStrength"},"matchType":match_type,"similarity":f'{chosen["nameSimilarity"]:.3f}',"contextScore":f'{chosen["contextScore"]:.3f}'})
        stats["matched"]+=1
        stats[match_type]+=1
        if "toponymic_" in chosen.get("rule",""):
            stats["toponymic_matched"]+=1
        if chosen.get("rule")=="toponymic_anchor":
            stats["anchor_matched"]+=1
        if chosen.get("rule")=="limes_anchor":
            stats["limes_anchor_matched"]+=1
        continue
    for rank,item in enumerate(candidates[:5],1):
        ambiguous_rows.append({**occ,"candidateRank":rank,**{k:v for k,v in item.items() if k!="contextStrength"},"similarity":f'{item["nameSimilarity"]:.3f}',"contextScore":f'{item["contextScore"]:.3f}'})
    stats["ambiguous"]+=1
BASE_FIELDS=["occurrenceId","document","chapter","sourceLine","placeName","placeSource","office","unit","declaredProvince","explicitProvince","hardProvince","softProvince","expectedProvince","region","contextText"]
CANDIDATE_FIELDS=["pleiadesId","pleiadesName","candidate","rule","tier","latitude","longitude","featureType","gisProvince","geojsonId","nearestProvince","nearestGeojsonId","nearestKm","nameSimilarity","contextStatus","contextScore"]
MATCH_FIELDS=BASE_FIELDS+CANDIDATE_FIELDS+["matchType","similarity"]
AMBIGUOUS_FIELDS=BASE_FIELDS+["candidateRank"]+CANDIDATE_FIELDS+["similarity"]
REJECTED_FIELDS=BASE_FIELDS+["candidateRank"]+CANDIDATE_FIELDS+["reason"]
CONFLICT_FIELDS=REJECTED_FIELDS
OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
for path,fields,rows in [
    (OCCURRENCE_OUTPUT,BASE_FIELDS,occurrences),
    (MATCH_OUTPUT,MATCH_FIELDS,match_rows),
    (AMBIGUOUS_OUTPUT,AMBIGUOUS_FIELDS,ambiguous_rows),
    (UNMATCHED_OUTPUT,BASE_FIELDS,unmatched_rows),
    (REJECTED_OUTPUT,REJECTED_FIELDS,rejected_rows),
    (CONFLICT_OUTPUT,CONFLICT_FIELDS,conflict_rows)
]:
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
print()
print("Living Notitia V4")
print("match_notitia_pleiades_xml_v12.py")
print()
print("XML                     :",XML_INPUT)
print("PlaceMention input      :",PLACEMENTION_INPUT)
print("PlaceMention rows       :",len(placemention_rows))
print("Eligible PlaceMentions  :",len(eligible_mentions))
print("Placeholder mentions    :",placeholder_mentions)
print("Pleiades names          :",len(name_rows))
print("Pleiades places         :",len(place_rows))
print("Province polygons       :",len(features))
print("Matched input mentions  :",len(occurrences))
print("Matched                 :",stats["matched"])
print("  CONTEXT_EXACT         :",stats["CONTEXT_EXACT"])
print("  CONTEXT_FUZZY         :",stats["CONTEXT_FUZZY"])
print("  CONTEXT_NEAR_EXACT    :",stats["CONTEXT_NEAR_EXACT"])
print("  CONTEXT_NEAR_FUZZY    :",stats["CONTEXT_NEAR_FUZZY"])
print("  CONTEXT_CONFLICT_EXACT:",stats["CONTEXT_CONFLICT_EXACT"])
print("  CONTEXT_CONFLICT_FUZZY:",stats["CONTEXT_CONFLICT_FUZZY"])
print("  REGION_EXACT          :",stats["REGION_EXACT"])
print("  REGION_FUZZY          :",stats["REGION_FUZZY"])
print("  REGION_NEAR_EXACT     :",stats["REGION_NEAR_EXACT"])
print("  REGION_NEAR_FUZZY     :",stats["REGION_NEAR_FUZZY"])
print("  FEATURE_EXACT         :",stats["FEATURE_EXACT"])
print("  FEATURE_FUZZY         :",stats["FEATURE_FUZZY"])
print("  EXACT_NO_CONTEXT      :",stats["EXACT_NO_CONTEXT"])
print("  FUZZY_NO_CONTEXT      :",stats["FUZZY_NO_CONTEXT"])
print("Ambiguous occurrences   :",stats["ambiguous"])
print("Unmatched occurrences   :",stats["unmatched"])
print("Rejected occurrences    :",stats["rejected_occurrences"])
print("Toponymic matches       :",stats["toponymic_matched"])
print("Anchor occurrences      :",stats["anchor_occurrences"])
print("Anchor matches          :",stats["anchor_matched"])
print("Limes anchor matches    :",stats["limes_anchor_matched"])
print()
print("Occurrence output       :",OCCURRENCE_OUTPUT)
print("Match output            :",MATCH_OUTPUT)
print("Ambiguous output        :",AMBIGUOUS_OUTPUT)
print("Unmatched output        :",UNMATCHED_OUTPUT)
print("Rejected output         :",REJECTED_OUTPUT)
print("Conflict audit output   :",CONFLICT_OUTPUT)
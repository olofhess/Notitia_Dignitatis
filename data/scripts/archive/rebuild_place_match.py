#
# Living Notitia V3
# rebuild_place_match.py
#
from pathlib import Path
import csv
import re
HERE=Path(__file__).resolve()
ROOT=next((p for p in HERE.parents if (p/"csv"/"Place.csv").exists()),None)
if ROOT is None:
    raise FileNotFoundError("Kan inte hitta projektroten med csv/Place.csv")
PLACE_INPUT=ROOT/"csv"/"Place.csv"
PROVINCE_INPUT=ROOT/"csv"/"ProvinceMatch.csv"
PLEIADES_INPUT=ROOT/"csv"/"PleiadesName.csv"
MATCH_OUTPUT=ROOT/"csv"/"PlaceMatch.csv"
AMBIGUOUS_OUTPUT=ROOT/"csv"/"PlaceAmbiguous.csv"
UNMATCHED_OUTPUT=ROOT/"csv"/"PlaceUnmatched.csv"
MATCH_FIELDS=[
    "placeName",
    "component",
    "candidate",
    "rule",
    "pleiadesId",
    "pleiadesName",
    "matchType"
]
AMBIGUOUS_FIELDS=[
    "placeName",
    "component",
    "candidate",
    "rule",
    "pleiadesId",
    "pleiadesName"
]
UNMATCHED_FIELDS=[
    "placeName",
    "component"
]
WORD_RULES={
    "Aquileiae":"Aquileia",
    "Palmira":"Palmyra",
    "Singiduno":"Singidunum",
    "Ravennae":"Ravenna",
    "Lauriaco":"Lauriacum",
    "Mediolana":"Mediolanum",
    "Mogontiaco":"Mogontiacum",
    "Viminacio":"Viminacium",
    "Marcianopoli":"Marcianopolis",
    "Maximianopoli":"Maximianopolis",
    "Trapezunta":"Trapezus",
    "Nicomediae":"Nicomedia",
    "Antiochiae":"Antiochia",
    "Damasci":"Damascus",
    "Pelusio":"Pelusium",
    "Copto":"Coptos",
    "Memfi":"Memphis",
    "Thebas":"Thebae"
}
ENDINGS=[
    ("ae","a"),
    ("o","um"),
    ("i","us"),
    ("am","a"),
    ("em","is")
]
ADMIN_NAMES={
    "africa",
    "africae",
    "gallia",
    "galliae",
    "gallias",
    "galliarum",
    "italia",
    "italiae",
    "italiam",
    "illyricum",
    "illyrici",
    "hispania",
    "hispaniae",
    "hispanias",
    "hispaniarum",
    "britannia",
    "britanniae",
    "britannias",
    "britanniarum",
    "oriens",
    "orientis",
    "asiana",
    "asianae",
    "pontica",
    "ponticae",
    "thraciarum",
    "macedoniae",
    "daciarum",
    "pannoniarum",
    "aegypti",
    "septem provinciarum",
    "dalmatiae",
    "norici mediterranei",
    "norici ripensis",
    "norici mediterranei et ripensis"
}
IGNORE_PREFIXES=(
    "aut ",
    "ceteros ",
    "consultationes ",
    "ali ",
    "alio ",
    "apud ",
    "iuxta ",
    "nunc ",
    "nune ",
    "regionis ",
    "provincia ",
    "provinciae ",
    "dioecesis ",
    "dioceseos "
)
IGNORE_CONTAINS=(
    " dictat ",
    " tractat ",
    " respondet ",
    " emittit ",
    " offici",
    " palatinos",
    " scriniarios",
    " graecum",
    " annotationes",
    " legationes",
    " deputati",
    " consultationes ",
    " preces ",
    " principem ",
    " princeps "
)
DESCRIPTION_FIRST={
    "a",
    "ab",
    "ad",
    "ali",
    "alio",
    "apud",
    "circa",
    "contra",
    "ex",
    "in",
    "infra",
    "inter",
    "intra",
    "iuxta",
    "per",
    "post",
    "praeter",
    "pro",
    "prope",
    "propter",
    "secus",
    "sub",
    "super",
    "supra",
    "trans",
    "ultra",
    "usque"
}
def clean(text):
    text=str(text or "")
    text=re.sub(r"^\(.*?\)\s*","",text)
    text=re.sub(r"^\.+\s*","",text)
    text=" ".join(text.split())
    return text.strip(" .,;:-()")
def lower(text):
    return clean(text).lower()
province_names=set()
with open(PROVINCE_INPUT,newline="",encoding="utf-8") as f:
    reader=csv.DictReader(f)
    for row in reader:
        name=clean(row.get("notitiaMatch",""))
        if name:
            province_names.add(name.lower())
macro_names=set(province_names)
macro_names.update(ADMIN_NAMES)
province_suffixes=sorted(
    province_names,
    key=len,
    reverse=True
)
def is_nonplace(name):
    name=clean(name)
    if not name:
        return True
    lname=name.lower()
    padded=" "+lname+" "
    if lname in macro_names:
        return True
    if "[" in name or "]" in name or "?" in name:
        return True
    if re.fullmatch(r"\.+",name):
        return True
    if lname.startswith(IGNORE_PREFIXES):
        return True
    if any(x in padded for x in IGNORE_CONTAINS):
        return True
    words=lname.split()
    if len(words)>1 and words[0] in DESCRIPTION_FIRST:
        return True
    return False
def strip_province_suffix(text):
    text=clean(text)
    ltext=text.lower()
    for province in province_suffixes:
        suffix=" "+province
        if ltext.endswith(suffix):
            return clean(text[:-len(suffix)])
    return text
def split_components(place_name):
    text=clean(place_name)
    text=strip_province_suffix(text)
    if not text:
        return []
    if lower(place_name) in macro_names:
        return []
    components=[]
    for part in re.split(r"\s+et\s+",text,flags=re.IGNORECASE):
        part=strip_province_suffix(part)
        part=clean(part)
        if not part:
            continue
        if lower(part) in macro_names:
            continue
        components.append(part)
    if not components and not is_nonplace(text):
        components=[text]
    result=[]
    seen=set()
    for component in components:
        key=component.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(component)
    return result
def candidate_variants(component):
    variants=[]
    seen=set()
    def add(candidate,rule):
        candidate=strip_province_suffix(candidate)
        candidate=clean(candidate)
        if not candidate:
            return
        if lower(candidate) in macro_names:
            return
        key=candidate.lower()
        if key in seen:
            return
        seen.add(key)
        variants.append((candidate,rule))
    add(component,"original")
    for splitter in [" siue "," sive "," - "]:
        if splitter in component:
            for part in component.split(splitter):
                add(part,"alias")
    match=re.match(r"^(.*?)\s+in\s+.+$",component,flags=re.IGNORECASE)
    if match:
        add(match.group(1),"before_in")
    for candidate,_ in list(variants):
        words=candidate.split()
        if len(words)>1:
            add(words[0],"first_word")
    for candidate,_ in list(variants):
        first=candidate.split()[0]
        if first in WORD_RULES:
            add(WORD_RULES[first],"word_rule")
        for old,new in ENDINGS:
            if first.endswith(old) and len(first)>len(old):
                add(first[:-len(old)]+new,"ending")
    return variants
pleiades_index={}
with open(PLEIADES_INPUT,newline="",encoding="utf-8") as f:
    reader=csv.DictReader(f)
    for row in reader:
        name=clean(row.get("romanized",""))
        pid=clean(row.get("pleiadesId",""))
        if not name or not pid:
            continue
        pleiades_index.setdefault(name.lower(),[]).append(row)
place_names=[]
seen_places=set()
excluded_macro=[]
excluded_other=[]
with open(PLACE_INPUT,newline="",encoding="utf-8") as f:
    reader=csv.DictReader(f)
    for row in reader:
        place_name=clean(row.get("placeName",""))
        if not place_name:
            continue
        key=place_name.lower()
        if key in seen_places:
            continue
        seen_places.add(key)
        if key in macro_names:
            excluded_macro.append(place_name)
            continue
        if is_nonplace(place_name):
            excluded_other.append(place_name)
            continue
        place_names.append(place_name)
match_rows=[]
ambiguous_rows=[]
unmatched_rows=[]
matched_components=0
ambiguous_components=0
unmatched_components=0
component_count=0
for place_name in place_names:
    components=split_components(place_name)
    if not components:
        continue
    for component in components:
        component_count+=1
        hits={}
        evidence={}
        for candidate,rule in candidate_variants(component):
            matches=pleiades_index.get(candidate.lower(),[])
            for match in matches:
                pid=clean(match.get("pleiadesId",""))
                pname=clean(match.get("romanized",""))
                if not pid:
                    continue
                hits[pid]=pname
                evidence.setdefault(pid,[]).append((candidate,rule))
        if len(hits)==0:
            unmatched_components+=1
            unmatched_rows.append({
                "placeName":place_name,
                "component":component
            })
            continue
        if len(hits)==1:
            matched_components+=1
            pid=next(iter(hits))
            candidate,rule=evidence[pid][0]
            match_rows.append({
                "placeName":place_name,
                "component":component,
                "candidate":candidate,
                "rule":rule,
                "pleiadesId":pid,
                "pleiadesName":hits[pid],
                "matchType":"CONFIRMED"
            })
            continue
        ambiguous_components+=1
        for pid in sorted(hits):
            candidate,rule=evidence[pid][0]
            ambiguous_rows.append({
                "placeName":place_name,
                "component":component,
                "candidate":candidate,
                "rule":rule,
                "pleiadesId":pid,
                "pleiadesName":hits[pid]
            })
match_rows.sort(
    key=lambda r:(
        r["placeName"].lower(),
        r["component"].lower(),
        r["pleiadesId"]
    )
)
ambiguous_rows.sort(
    key=lambda r:(
        r["placeName"].lower(),
        r["component"].lower(),
        r["pleiadesId"]
    )
)
unmatched_rows.sort(
    key=lambda r:(
        r["placeName"].lower(),
        r["component"].lower()
    )
)
with open(MATCH_OUTPUT,"w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=MATCH_FIELDS)
    writer.writeheader()
    writer.writerows(match_rows)
with open(AMBIGUOUS_OUTPUT,"w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=AMBIGUOUS_FIELDS)
    writer.writeheader()
    writer.writerows(ambiguous_rows)
with open(UNMATCHED_OUTPUT,"w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=UNMATCHED_FIELDS)
    writer.writeheader()
    writer.writerows(unmatched_rows)
print()
print("Living Notitia V3")
print("rebuild_place_match.py")
print()
print("Unique names in Place.csv :",len(seen_places))
print("Excluded macro geography :",len(excluded_macro))
print("Excluded other           :",len(excluded_other))
print("Source names processed   :",len(place_names))
print("Place components         :",component_count)
print("Confirmed components     :",matched_components)
print("Ambiguous components     :",ambiguous_components)
print("Unmatched components     :",unmatched_components)
print("PlaceMatch rows          :",len(match_rows))
print("PlaceAmbiguous rows      :",len(ambiguous_rows))
print()
if excluded_macro:
    print("Excluded macro geography:")
    for name in sorted(excluded_macro,key=str.lower):
        print(" ",name)
    print()
print("Match output     :",MATCH_OUTPUT)
print("Ambiguous output :",AMBIGUOUS_OUTPUT)
print("Unmatched output :",UNMATCHED_OUTPUT)
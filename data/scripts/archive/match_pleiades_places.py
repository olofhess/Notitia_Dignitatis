#
# Living Notitia
# match_pleiades_places.py
#

from pathlib import Path
import csv
import json
import re
import unicodedata
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[3]

CANDIDATES=ROOT/"csv"/"PlaceCandidate.csv"
PLEIADES=ROOT/"data"/"pleiades-places.json"
OUTPUT=ROOT/"csv"/"PleiadesMatch.csv"

def normalize(text):
    if not text:
        return ""
    text=unicodedata.normalize("NFKD",text)
    text="".join(
        c for c in text
        if not unicodedata.combining(c)
    )
    text=text.lower().strip()
    text=re.sub(r"[.,;:()\[\]]"," ",text)
    text=re.sub(r"\s+"," ",text)
    return text

def latin_variants(name):
    n=normalize(name)
    variants={n}
    endings={
        "ae":"a",
        "iae":"ia",
        "ii":"ium",
        "orum":"i",
        "arum":"a",
        "ensis":"ensis",
        "enses":"ensis"
    }
    for ending,replacement in endings.items():
        if n.endswith(ending):
            variants.add(
                n[:-len(ending)]+replacement
            )
    return variants

print()
print("Living Notitia")
print("match_pleiades_places.py")
print()

candidates=[]

with open(
    CANDIDATES,
    encoding="utf-8"
) as f:
    reader=csv.DictReader(f)
    for row in reader:
        candidates.append(row)

print(
    "Candidates :",
    len(candidates)
)

candidateVariants={}

for row in candidates:
    name=row.get("placeName","").strip()
    if not name:
        continue
    candidateVariants[name]=latin_variants(name)

nameIndex=defaultdict(list)

print(
    "Reading Pleiades:",
    PLEIADES
)

with open(
    PLEIADES,
    encoding="utf-8"
) as f:
    data=json.load(f)

if isinstance(data,dict) and "@graph" in data:
    places=data["@graph"]
elif isinstance(data,dict) and "features" in data:
    places=data["features"]
elif isinstance(data,list):
    places=data
else:
    places=[]

print(
    "Pleiades places:",
    len(places)
)

for place in places:
    if not isinstance(place,dict):
        continue
    props=place.get(
        "properties",
        place
    )
    pid=(
        place.get("id")
        or props.get("id")
        or props.get("uri")
        or ""
    )
    names=set()
    title=props.get("title")
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
    rawNames=props.get("names",[])
    if isinstance(rawNames,list):
        for item in rawNames:
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
                        names.update(
                            str(x)
                            for x in value
                            if x
                        )
    for name in names:
        norm=normalize(name)
        if norm:
            nameIndex[norm].append(
                {
                    "id":pid,
                    "title":title or name,
                    "matchedName":name
                }
            )

print(
    "Indexed names:",
    len(nameIndex)
)

results=[]

exactCount=0
variantCount=0
ambiguousCount=0
unmatchedCount=0

for row in candidates:
    placeName=row.get(
        "placeName",
        ""
    ).strip()
    if not placeName:
        continue
    exact=normalize(placeName)
    matches=nameIndex.get(
        exact,
        []
    )
    method=""
    matchedVariant=""
    if matches:
        method="EXACT"
        matchedVariant=exact
    else:
        found=[]
        for variant in latin_variants(
            placeName
        ):
            if variant==exact:
                continue
            if variant in nameIndex:
                found.extend(
                    nameIndex[variant]
                )
                matchedVariant=variant
        unique={}
        for match in found:
            key=(
                match["id"],
                match["matchedName"]
            )
            unique[key]=match
        matches=list(
            unique.values()
        )
        if matches:
            method="LATIN_VARIANT"
    if not matches:
        status="UNMATCHED"
        unmatchedCount+=1
        results.append({
            **row,
            "status":status,
            "method":"",
            "pleiadesId":"",
            "pleiadesTitle":"",
            "matchedName":"",
            "matchCount":0
        })
        continue
    ids=set(
        str(m["id"])
        for m in matches
    )
    if len(ids)>1:
        status="AMBIGUOUS"
        ambiguousCount+=1
    else:
        status="MATCH"
        if method=="EXACT":
            exactCount+=1
        else:
            variantCount+=1
    results.append({
        **row,
        "status":status,
        "method":method,
        "pleiadesId":" | ".join(
            sorted(ids)
        ),
        "pleiadesTitle":" | ".join(
            sorted(
                set(
                    str(m["title"])
                    for m in matches
                )
            )
        ),
        "matchedName":" | ".join(
            sorted(
                set(
                    str(m["matchedName"])
                    for m in matches
                )
            )
        ),
        "matchCount":len(ids)
    })

fields=list(
    candidates[0].keys()
)

fields += [
    "status",
    "method",
    "pleiadesId",
    "pleiadesTitle",
    "matchedName",
    "matchCount"
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
    writer.writerows(results)

print()
print("Results")
print("--------------------------------")
print(
    "Exact       :",
    exactCount
)
print(
    "Latin form  :",
    variantCount
)
print(
    "Ambiguous   :",
    ambiguousCount
)
print(
    "Unmatched   :",
    unmatchedCount
)
print()
print(
    "Output:",
    OUTPUT
)
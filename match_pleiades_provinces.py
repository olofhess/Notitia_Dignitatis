#
# Living Notitia
# match_pleiades_provinces.py
#

from pathlib import Path
import csv
import json
import re
import unicodedata
from difflib import SequenceMatcher

ROOT=Path(__file__).resolve().parent

INPUT=ROOT/"csv"/"ProvinceUnmatched.csv"
PLEIADES=ROOT/"data"/"pleiades-places.json"
OUTPUT=ROOT/"csv"/"ProvincePleiadesMatch.csv"

def normalize(text):
    if not text:
        return ""
    text=unicodedata.normalize("NFKD",text)
    text="".join(
        c for c in text
        if not unicodedata.combining(c)
    )
    text=text.lower().strip()
    text=text.replace("ph","f")
    text=text.replace("y","i")
    text=text.replace("v","u")
    text=re.sub(r"[^a-z0-9 ]"," ",text)
    text=re.sub(r"\s+"," ",text)
    return text

def latin_variants(text):
    n=normalize(text)
    variants={n}
    words=n.split()
    if not words:
        return variants
    endings=[
        ("iae","ia"),
        ("ae","a"),
        ("arum","a"),
        ("orum","um"),
        ("ensis","ensis"),
        ("enses","ensis"),
        ("i","us")
    ]
    last=words[-1]
    for old,new in endings:
        if last.endswith(old):
            changed=last[:-len(old)]+new
            variants.add(
                " ".join(
                    words[:-1]+[changed]
                )
            )
    return variants

print()
print("Living Notitia")
print("match_pleiades_provinces.py")
print()

with open(
    INPUT,
    encoding="utf-8"
) as f:
    provinces=list(
        csv.DictReader(f)
    )

print(
    "Unmatched provinces:",
    len(provinces)
)

print(
    "Reading Pleiades:",
    PLEIADES
)

with open(
    PLEIADES,
    encoding="utf-8"
) as f:
    data=json.load(f)

places=data.get(
    "@graph",
    []
)

print(
    "Pleiades records:",
    len(places)
)

records=[]

for place in places:

    if not isinstance(place,dict):
        continue

    pid=(
        place.get("id")
        or place.get("uri")
        or ""
    )

    title=place.get(
        "title",
        ""
    )

    description=place.get(
        "description",
        ""
    )

    placeTypes=place.get(
        "placeTypes",
        []
    )

    names=set()

    if title:
        names.add(title)

    for key in [
        "name",
        "nameAttested",
        "nameRomanized",
        "attested",
        "romanized"
    ]:

        value=place.get(key)

        if isinstance(value,str):
            names.add(value)

        elif isinstance(value,list):
            for item in value:
                if isinstance(item,str):
                    names.add(item)

    rawNames=place.get(
        "names",
        []
    )

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
                        for name in value:
                            if name:
                                names.add(str(name))

    if not names:
        continue

    records.append({
        "id":pid,
        "title":title,
        "description":description,
        "placeTypes":" | ".join(
            str(x)
            for x in placeTypes
        ),
        "names":names
    })

print(
    "Pleiades named records:",
    len(records)
)

results=[]

for province in provinces:

    sourceName=province[
        "provinceName"
    ].strip()

    sourceVariants=latin_variants(sourceName)

    candidates=[]

    for record in records:

        bestScore=0
        bestName=""
        bestMethod=""

        for pleiadesName in record["names"]:

            pnorm=normalize(
                pleiadesName
            )

            if not pnorm:
                continue

            if pnorm in sourceVariants:

                score=1.0
                method="NORMALIZED"

            else:

                score=max(
                    SequenceMatcher(
                        None,
                        variant,
                        pnorm
                    ).ratio()
                    for variant
                    in sourceVariants
                )

                method="SIMILAR"

            if score>bestScore:

                bestScore=score
                bestName=pleiadesName
                bestMethod=method

        if bestScore>=0.70:

            candidates.append({
                "score":bestScore,
                "method":bestMethod,
                "id":record["id"],
                "title":record["title"],
                "matchedName":bestName,
                "description":record[
                    "description"
                ],
                "placeTypes":record[
                    "placeTypes"
                ]
            })

    candidates.sort(
        key=lambda x:x["score"],
        reverse=True
    )

    candidates=candidates[:5]

    if not candidates:

        results.append({
            **province,
            "rank":"",
            "score":"",
            "method":"",
            "pleiadesId":"",
            "pleiadesTitle":"",
            "matchedName":"",
            "placeTypes":"",
            "description":""
        })

        continue

    for rank,candidate in enumerate(
        candidates,
        start=1
    ):

        results.append({
            **province,
            "rank":rank,
            "score":f"{candidate['score']:.3f}",
            "method":candidate[
                "method"
            ],
            "pleiadesId":candidate[
                "id"
            ],
            "pleiadesTitle":candidate[
                "title"
            ],
            "matchedName":candidate[
                "matchedName"
            ],
            "placeTypes":candidate[
                "placeTypes"
            ],
            "description":candidate[
                "description"
            ]
        })

fields=[
    "sourceLine",
    "provinceName",
    "rank",
    "score",
    "method",
    "pleiadesId",
    "pleiadesTitle",
    "matchedName",
    "placeTypes",
    "description"
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

matched=len(
    {
        row["provinceName"]
        for row in results
        if row["pleiadesId"]
    }
)

print()
print("Results")
print("--------------------------------")
print(
    "Provinces       :",
    len(provinces)
)
print(
    "With candidates :",
    matched
)
print(
    "No candidates   :",
    len(provinces)-matched
)
print()
print(
    "Output:",
    OUTPUT
)
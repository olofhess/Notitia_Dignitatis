#
# Living Notitia
# inspect_gis_provinces.py
#

from pathlib import Path
import csv
import json
import re

ROOT=Path(__file__).resolve().parents[1]

GEOJSON=ROOT/"data"/"provinces.geojson"
NOTITIA=ROOT/"data"/"Province.csv"
OUTPUT=ROOT/"data"/"GISProvinceReport.csv"

FIELDS=[
"gisProvince",
"canonicalName",
"notitiaMatch",
"status"
]

#
# Historisk synonymtabell.
# Ny kunskap läggs här – inte i parsern.
#

CANONICAL={

"ACHAIA":"ACHAIA",
"ACHAIAE":"ACHAIA",

"ASIA":"ASIA",
"ASIAE":"ASIA",

"BAETICA":"BAETICA",
"BAETICAE":"BAETICA",

"BITHYNIA":"BITHYNIA",
"BITHYNIAE":"BITHYNIA",

"CAMPANIA":"CAMPANIA",
"CAMPANIAE":"CAMPANIA",

"CORSICA":"CORSICA",
"CORSICAE":"CORSICA",

"CRETA":"CRETA",
"CRETAE":"CRETA",

"CYPRUS":"CYPRUS",
"CYPRI":"CYPRUS",

"EUROPA":"EUROPA",
"EUROPAE":"EUROPA",

"GALATIA":"GALATIA",
"GALATIAE":"GALATIA",

"LUSITANIA":"LUSITANIA",
"LUSITANIAE":"LUSITANIA",

"MACEDONIA":"MACEDONIA",
"MACEDONIAE":"MACEDONIA",

"MESOPOTAMIA":"MESOPOTAMIA",
"MESOPOTAMIAE":"MESOPOTAMIA",

"PALAESTINA":"PALAESTINA",
"PALAESTINAE":"PALAESTINA",

"PISIDIA":"PISIDIA",
"PISIDIAE":"PISIDIA",

"SCYTHIA":"SCYTHIA",
"SCYTHIAE":"SCYTHIA",

"SICILIA":"SICILIA",
"SICILIAE":"SICILIA",

"THESSALIA":"THESSALIA",
"THESSALIAE":"THESSALIA",

"THRACIA":"THRACIA",
"THRACIAE":"THRACIA",

"VALERIA":"VALERIA",
"VALERIAE":"VALERIA",

"SARDINIA":"SARDINIA",
"SARADINIAE":"SARDINIA",

"PAPHLAGONIA":"PAPHLAGONIA",
"PAFLAGONIAE":"PAPHLAGONIA",

"PHOENICE":"PHOENICE",
"FOENICIS":"PHOENICE",

"RHODOPE":"RHODOPE",
"RHODOPAE":"RHODOPE",

"HELLESPONTUS":"HELLESPONTUS",
"HELENOPONTI":"HELLESPONTUS",

"PRAEVALITANA":"PRAEVALITANA",
"PRAEUALITANAE":"PRAEVALITANA",

"CALLAECIA":"GALLAECIA",
"CALLAECIAE":"GALLAECIA"

}

#
# Endast teknisk normalisering
#

def normalize(name):

    name=name.upper()

    name=name.replace("Æ","AE")
    name=name.replace("Œ","OE")

    name=name.replace("\n"," ")

    name=re.sub(r"[.,;:()]","",name)

    name=" ".join(name.split())

    return name


def canonical(name):

    name=normalize(name)

    return CANONICAL.get(name,name)


if not GEOJSON.exists():
    raise FileNotFoundError(GEOJSON)

with open(GEOJSON,encoding="utf-8-sig") as f:
    geo=json.load(f)

notitia=[]

with open(NOTITIA,newline="",encoding="utf-8") as f:

    reader=csv.DictReader(f)

    for row in reader:

        province=row["provinceName"].strip()

        notitia.append({

            "name":province,
            "canonical":canonical(province)

        })

rows=[]

matched=0
unmatched=0

for feature in sorted(
    geo["features"],
    key=lambda x:x["properties"]["PROV_NAME"]
):

    gis=feature["properties"]["PROV_NAME"].strip()

    key=canonical(gis)

    match=""
    status="NONE"

    for province in notitia:

        if province["canonical"]==key:

            match=province["name"]
            status="MATCH"
            matched+=1
            break

    if status=="NONE":
        unmatched+=1

    rows.append({

        "gisProvince":gis,
        "canonicalName":key,
        "notitiaMatch":match,
        "status":status

    })

with open(OUTPUT,"w",newline="",encoding="utf-8") as f:

    writer=csv.DictWriter(f,fieldnames=FIELDS)

    writer.writeheader()
    writer.writerows(rows)

print()
print("Living Notitia")
print("inspect_gis_provinces.py")
print()
print(f"GIS provinces : {len(rows)}")
print(f"Matched       : {matched}")
print(f"Unmatched     : {unmatched}")
print()
print(f"Output : {OUTPUT}")
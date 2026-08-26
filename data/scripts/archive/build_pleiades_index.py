#
# Living Notitia V3
# build_pleiades_index.py
#

from pathlib import Path
import csv
import json

ROOT=Path(__file__).resolve().parents[1]

INPUT=ROOT/"data"/"pleiades-places.json"

PLACE_OUTPUT=ROOT/"csv"/"PleiadesPlace.csv"
NAME_OUTPUT=ROOT/"csv"/"PleiadesName.csv"

PLACE_FIELDS=[
"pleiadesId",
"title",
"latitude",
"longitude",
"featureType",
"description",
"uri"
]

NAME_FIELDS=[
"pleiadesId",
"romanized",
"attested",
"language",
"nameType"
]

with open(INPUT,encoding="utf-8") as f:
    data=json.load(f)

graph=data["@graph"]

placeRows=[]
nameRows=[]

def get_place_id(place):

    uri=place.get("uri","")

    if uri:
        return uri.rstrip("/").split("/")[-1],uri

    for location in place.get("locations",[]):

        uri=location.get("uri","")

        if "/places/" in uri:

            pid=uri.split("/places/")[1].split("/")[0]

            return pid,uri

    for name in place.get("names",[]):

        uri=name.get("uri","")

        if "/places/" in uri:

            pid=uri.split("/places/")[1].split("/")[0]

            return pid,uri

    return "",""

for place in graph:

    pleiadesId,uri=get_place_id(place)

    title=place.get("title","")

    description=place.get("description","")

    latitude=""
    longitude=""
    featureType=""

    for location in place.get("locations",[]):

        if not isinstance(location,dict):
            continue

        geometry=location.get("geometry")

        if isinstance(geometry,dict):

            coordinates=geometry.get("coordinates",[])

            if isinstance(coordinates,list) and len(coordinates)>=2:

                longitude=coordinates[0]
                latitude=coordinates[1]

        features=location.get("featureType")

        if isinstance(features,list) and features:

            featureType=";".join(features)

        if latitude!="" and featureType!="":
            break

    placeRows.append({

        "pleiadesId":pleiadesId,
        "title":title,
        "latitude":latitude,
        "longitude":longitude,
        "featureType":featureType,
        "description":description,
        "uri":uri

    })

    for name in place.get("names",[]):

        if not isinstance(name,dict):
            continue

        nameRows.append({

            "pleiadesId":pleiadesId,
            "romanized":name.get("romanized",""),
            "attested":name.get("attested",""),
            "language":name.get("language",""),
            "nameType":name.get("nameType","")

        })


placeRows.sort(
    key=lambda r:(
        r["title"].lower(),
        r["pleiadesId"]
    )
)

nameRows.sort(
    key=lambda r:(
        r["romanized"].lower(),
        r["pleiadesId"]
    )
)

with open(
    PLACE_OUTPUT,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer=csv.DictWriter(
        f,
        fieldnames=PLACE_FIELDS
    )

    writer.writeheader()
    writer.writerows(placeRows)

with open(
    NAME_OUTPUT,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer=csv.DictWriter(
        f,
        fieldnames=NAME_FIELDS
    )

    writer.writeheader()
    writer.writerows(nameRows)

print()
print("Pleiades places :",len(placeRows))
print("Pleiades names  :",len(nameRows))
print()
print("Place output :",PLACE_OUTPUT)
print("Name output  :",NAME_OUTPUT)
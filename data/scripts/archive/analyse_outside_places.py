#
# Living Notitia V3
# analyse_outside_places.py
#
from pathlib import Path
import csv
import json
import math
HERE=Path(__file__).resolve()
ROOT=next((p for p in HERE.parents if (p/"csv"/"PlaceProvince.csv").exists()),None)
if ROOT is None:
    raise FileNotFoundError("Kan inte hitta projektroten med csv/PlaceProvince.csv")
PLACE_INPUT=ROOT/"csv"/"PlaceProvince.csv"
GEOJSON_INPUT=ROOT/"data"/"provinces.geojson"
OUTPUT=ROOT/"csv"/"OutsideNearestProvince.csv"
if not GEOJSON_INPUT.exists():
    raise FileNotFoundError("Kan inte hitta "+str(GEOJSON_INPUT))
FIELDS=[
    "placeName",
    "pleiadesId",
    "latitude",
    "longitude",
    "nearestProvince",
    "geojsonId",
    "distanceKm",
    "segmentStartLat",
    "segmentStartLon",
    "segmentEndLat",
    "segmentEndLon"
]
EARTH_RADIUS_KM=6371.0088
def to_float(value):
    try:
        return float(str(value).strip())
    except (TypeError,ValueError):
        return None
def point_segment_distance_km(lat,lon,lat1,lon1,lat2,lon2):
    lat0=math.radians(lat)
    cos_lat=math.cos(lat0)
    x1=EARTH_RADIUS_KM*math.radians(lon1-lon)*cos_lat
    y1=EARTH_RADIUS_KM*math.radians(lat1-lat)
    x2=EARTH_RADIUS_KM*math.radians(lon2-lon)*cos_lat
    y2=EARTH_RADIUS_KM*math.radians(lat2-lat)
    dx=x2-x1
    dy=y2-y1
    length2=dx*dx+dy*dy
    if length2==0:
        return math.hypot(x1,y1)
    t=-(x1*dx+y1*dy)/length2
    if t<0:
        t=0
    elif t>1:
        t=1
    closest_x=x1+t*dx
    closest_y=y1+t*dy
    return math.hypot(closest_x,closest_y)
def geometry_rings(geometry):
    if not geometry:
        return []
    geometry_type=geometry.get("type","")
    coordinates=geometry.get("coordinates",[])
    if geometry_type=="Polygon":
        if coordinates:
            return [coordinates[0]]
        return []
    if geometry_type=="MultiPolygon":
        rings=[]
        for polygon in coordinates:
            if polygon:
                rings.append(polygon[0])
        return rings
    return []
with open(GEOJSON_INPUT,encoding="utf-8") as f:
    geojson=json.load(f)
provinces=[]
for feature in geojson.get("features",[]):
    properties=feature.get("properties",{})
    province_name=str(properties.get("PROV_NAME","")).strip()
    if not province_name:
        continue
    geojson_id=str(properties.get("OBJECTID",feature.get("id",""))).strip()
    rings=geometry_rings(feature.get("geometry"))
    if not rings:
        continue
    provinces.append({
        "provinceName":province_name,
        "geojsonId":geojson_id,
        "rings":rings
    })
outside=[]
with open(PLACE_INPUT,newline="",encoding="utf-8") as f:
    reader=csv.DictReader(f)
    for row in reader:
        if row.get("status","").strip()!="OUTSIDE":
            continue
        lat=to_float(row.get("latitude",""))
        lon=to_float(row.get("longitude",""))
        if lat is None or lon is None:
            continue
        outside.append({
            "placeName":row.get("placeName","").strip(),
            "pleiadesId":row.get("pleiadesId","").strip(),
            "latitude":lat,
            "longitude":lon
        })
results=[]
for place in outside:
    best_distance=None
    best_province=None
    best_segment=None
    lat=place["latitude"]
    lon=place["longitude"]
    for province in provinces:
        for ring in province["rings"]:
            if len(ring)<2:
                continue
            for i in range(1,len(ring)):
                lon1=float(ring[i-1][0])
                lat1=float(ring[i-1][1])
                lon2=float(ring[i][0])
                lat2=float(ring[i][1])
                distance=point_segment_distance_km(
                    lat,lon,
                    lat1,lon1,
                    lat2,lon2
                )
                if best_distance is None or distance<best_distance:
                    best_distance=distance
                    best_province=province
                    best_segment=(lat1,lon1,lat2,lon2)
            if ring[0]!=ring[-1]:
                lon1=float(ring[-1][0])
                lat1=float(ring[-1][1])
                lon2=float(ring[0][0])
                lat2=float(ring[0][1])
                distance=point_segment_distance_km(
                    lat,lon,
                    lat1,lon1,
                    lat2,lon2
                )
                if best_distance is None or distance<best_distance:
                    best_distance=distance
                    best_province=province
                    best_segment=(lat1,lon1,lat2,lon2)
    if best_province is None:
        continue
    results.append({
        "placeName":place["placeName"],
        "pleiadesId":place["pleiadesId"],
        "latitude":place["latitude"],
        "longitude":place["longitude"],
        "nearestProvince":best_province["provinceName"],
        "geojsonId":best_province["geojsonId"],
        "distanceKm":round(best_distance,2),
        "segmentStartLat":best_segment[0],
        "segmentStartLon":best_segment[1],
        "segmentEndLat":best_segment[2],
        "segmentEndLon":best_segment[3]
    })
results.sort(key=lambda r:r["distanceKm"])
with open(OUTPUT,"w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(results)
print()
print("Living Notitia V3")
print("analyse_outside_places.py")
print()
print("Province polygons :",len(provinces))
print("Outside places    :",len(outside))
print()
print("Nearest province:")
print()
for row in results:
    print(
        f'{row["placeName"]:<42}'
        f'{row["nearestProvince"]:<28}'
        f'{row["distanceKm"]:>9.2f} km'
    )
print()
print("Output :",OUTPUT)
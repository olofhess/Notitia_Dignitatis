#
# Living Notitia V3
# build_place_province.py
#
from pathlib import Path
import csv
import json
import math
ROOT=Path(__file__).resolve().parents[3]
PLACE_INPUT=ROOT/"csv"/"PlaceGazetteer.csv"
GEOJSON_INPUT=ROOT/"data"/"provinces.geojson"
OUTPUT=ROOT/"csv"/"PlaceProvince.csv"
NEAR_LIMIT_KM=20.0
EARTH_RADIUS_KM=6371.0088
FIELDS=[
    "placeProvinceId",
    "gazetteerId",
    "placeName",
    "pleiadesId",
    "pleiadesName",
    "latitude",
    "longitude",
    "provinceName",
    "geojsonId",
    "status",
    "distanceKm"
]
def to_float(value):
    try:
        number=float(str(value).strip())
    except (TypeError,ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number
def point_in_ring(x,y,ring):
    inside=False
    if len(ring)<3:
        return False
    j=len(ring)-1
    for i in range(len(ring)):
        x1=float(ring[j][0])
        y1=float(ring[j][1])
        x2=float(ring[i][0])
        y2=float(ring[i][1])
        if (y1>y)!=(y2>y):
            intersection=x1+(y-y1)*(x2-x1)/(y2-y1)
            if x<intersection:
                inside=not inside
        j=i
    return inside
def point_in_polygon(x,y,polygon):
    if not polygon:
        return False
    if not point_in_ring(x,y,polygon[0]):
        return False
    for hole in polygon[1:]:
        if point_in_ring(x,y,hole):
            return False
    return True
def point_in_geometry(x,y,geometry):
    if not geometry:
        return False
    geometry_type=geometry.get("type","")
    coordinates=geometry.get("coordinates",[])
    if geometry_type=="Polygon":
        return point_in_polygon(x,y,coordinates)
    if geometry_type=="MultiPolygon":
        return any(point_in_polygon(x,y,polygon) for polygon in coordinates)
    return False
def exterior_rings(geometry):
    if not geometry:
        return []
    geometry_type=geometry.get("type","")
    coordinates=geometry.get("coordinates",[])
    if geometry_type=="Polygon":
        return [coordinates[0]] if coordinates else []
    if geometry_type=="MultiPolygon":
        return [polygon[0] for polygon in coordinates if polygon]
    return []
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
def nearest_province(lat,lon,provinces):
    best_province=None
    best_distance=None
    for province in provinces:
        for ring in province["rings"]:
            if len(ring)<2:
                continue
            points=ring
            for i in range(1,len(points)):
                lon1=float(points[i-1][0])
                lat1=float(points[i-1][1])
                lon2=float(points[i][0])
                lat2=float(points[i][1])
                distance=point_segment_distance_km(
                    lat,lon,lat1,lon1,lat2,lon2
                )
                if best_distance is None or distance<best_distance:
                    best_distance=distance
                    best_province=province
            if points[0]!=points[-1]:
                lon1=float(points[-1][0])
                lat1=float(points[-1][1])
                lon2=float(points[0][0])
                lat2=float(points[0][1])
                distance=point_segment_distance_km(
                    lat,lon,lat1,lon1,lat2,lon2
                )
                if best_distance is None or distance<best_distance:
                    best_distance=distance
                    best_province=province
    return best_province,best_distance
with open(GEOJSON_INPUT,encoding="utf-8") as f:
    geojson=json.load(f)
provinces=[]
for feature in geojson.get("features",[]):
    properties=feature.get("properties",{})
    province_name=str(properties.get("PROV_NAME","")).strip()
    if not province_name:
        continue
    geojson_id=str(
        properties.get("OBJECTID",feature.get("id",""))
    ).strip()
    geometry=feature.get("geometry")
    if not geometry:
        continue
    provinces.append({
        "provinceName":province_name,
        "geojsonId":geojson_id,
        "geometry":geometry,
        "rings":exterior_rings(geometry)
    })
rows=[]
without_coordinates=0
direct_count=0
near_count=0
outside_count=0
outside=[]
with open(PLACE_INPUT,newline="",encoding="utf-8") as f:
    reader=csv.DictReader(f)
    for place in reader:
        latitude=to_float(place.get("latitude",""))
        longitude=to_float(place.get("longitude",""))
        if latitude is None or longitude is None:
            without_coordinates+=1
            continue
        matches=[]
        for province in provinces:
            if point_in_geometry(
                longitude,
                latitude,
                province["geometry"]
            ):
                matches.append(province)
        if len(matches)>1:
            names=", ".join(
                p["provinceName"] for p in matches
            )
            raise RuntimeError(
                "Platsen "
                +place.get("placeName","")
                +" träffar flera provinser: "
                +names
            )
        if len(matches)==1:
            province_name=matches[0]["provinceName"]
            geojson_id=matches[0]["geojsonId"]
            status="MATCH"
            distance_km=0.0
            direct_count+=1
        else:
            nearest,distance=nearest_province(
                latitude,
                longitude,
                provinces
            )
            if (
                nearest is not None
                and distance is not None
                and distance<=NEAR_LIMIT_KM
            ):
                province_name=nearest["provinceName"]
                geojson_id=nearest["geojsonId"]
                status="NEAR_MATCH"
                distance_km=distance
                near_count+=1
            else:
                province_name=""
                geojson_id=""
                status="OUTSIDE"
                distance_km=distance if distance is not None else ""
                outside_count+=1
                outside.append({
                    "placeName":place.get("placeName","").strip(),
                    "pleiadesId":place.get("pleiadesId","").strip(),
                    "latitude":latitude,
                    "longitude":longitude,
                    "distanceKm":distance
                })
        rows.append({
            "placeProvinceId":"",
            "gazetteerId":place.get("gazetteerId","").strip(),
            "placeName":place.get("placeName","").strip(),
            "pleiadesId":place.get("pleiadesId","").strip(),
            "pleiadesName":place.get("pleiadesName","").strip(),
            "latitude":place.get("latitude","").strip(),
            "longitude":place.get("longitude","").strip(),
            "provinceName":province_name,
            "geojsonId":geojson_id,
            "status":status,
            "distanceKm":(
                round(distance_km,2)
                if distance_km!=""
                else ""
            )
        })
rows.sort(
    key=lambda r:(
        r["provinceName"],
        r["placeName"].lower(),
        r["pleiadesId"]
    )
)
for number,row in enumerate(rows,1):
    row["placeProvinceId"]=f"PP{number:05d}"
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
with open(OUTPUT,"w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
print()
print("Living Notitia V3")
print("build_place_province.py")
print()
print("Province polygons :",len(provinces))
print("Places with coords:",len(rows))
print("MATCH             :",direct_count)
print("NEAR_MATCH        :",near_count)
print("Mapped total      :",direct_count+near_count)
print("OUTSIDE           :",outside_count)
print("Without coords    :",without_coordinates)
if outside:
    print()
    print("OUTSIDE:")
    for place in outside:
        print(
            place["placeName"],
            place["pleiadesId"],
            place["latitude"],
            place["longitude"],
            round(place["distanceKm"],2)
            if place["distanceKm"] is not None
            else ""
        )
print()
print("Near limit       :",NEAR_LIMIT_KM,"km")
print("Input places     :",PLACE_INPUT)
print("Input provinces  :",GEOJSON_INPUT)
print("Output           :",OUTPUT)
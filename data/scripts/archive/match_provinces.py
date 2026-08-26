#
# Living Notitia
# match_provinces.py
#

from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"

NOTITIA = ROOT / "csv" / "Province.csv"
GEOJSON = DATA / "provinces.geojson"
OUTPUT = ROOT / "csv" / "ProvinceMatch.csv"

MATCH = {

"Liguriae":"AEMILIA ET LIGURIA",

"Achaiae":"ACHAIA",
"Achaia":"ACHAIA",

"Apuliae et Calabriae":"APULIA ET CALABRIA",

"Arabiae":"ARABIA",
"Arabia":"ARABIA",

"Asiae":"ASIA",

"Baeticae":"BAETICA",
"Baetica":"BAETICA",

"Bithyniae":"BITHYNIA",
"Bithynia":"BITHYNIA",

"Callaeciae":"GALLAECIA",

"Campaniae":"CAMPANIA",
"Campania":"CAMPANIA",

"Cappadociae":"CAPPADOCIA",

"Cariae":"CARIA",
"Caria":"CARIA",

"Ciliciae":"CILICIA",
"Cilicia":"CILICIA",

"Corsicae":"CORSICA",

"Cretae":"CRETA",

"Cypri":"CYPRUS",

"Daciae mediterraneae":"DACIA MEDITERRANEA",
"Dacia mediterranea":"DACIA MEDITERRANEA",

"Daciae ripensis":"DACIA RIPENSIS",
"Dacia ripensis":"DACIA RIPENSIS",

"Dalmatiae":"DALMATIA",

"Dardaniae":"DARDANIA",
"Dardania":"DARDANIA",

"Epiri nouae":"EPIRUS NOVA",

"Epiri veteris":"EPIRUS VETUS",
"Epiri ueteris":"EPIRUS VETUS",

"Europae":"EUROPA",
"Europa":"EUROPA",

"Flaminiae et Piceni annonarii":"FLAMINIA ET PICENUM",

"Foenicis":"PHOENICE",
"Foenice":"PHOENICE",

"Galatiae":"GALATIA",
"Galatia":"GALATIA",

"Haemimonti":"HAEMIMONTUS",
"Haemimontus":"HAEMIMONTUS",

"Hellespontus":"HELLESPONTUS",

"Isauriae":"ISAURIA",
"Isauria":"ISAURIA",

"Libyae inferioris":"LIBYA INFERIOR",
"Libya inferior":"LIBYA INFERIOR",

"Libyae superioris":"LIBYA SUPERIOR",
"Libya superior":"LIBYA SUPERIOR",

"Lucaniae et Bruttiorum":"LUCANIA ET BRUTTII",
"Lucaniae et Brittiorum":"LUCANIA ET BRUTTII",

"Lusitaniae":"LUSITANIA",
"Lusitania":"LUSITANIA",

"Lyciae et Pamphyliae":"LYCIA ET PAMPHYLIA",

"Lydiae":"LYDIA",
"Lydia":"LYDIA",

"Macedoniae":"MACEDONIA",
"Macedonia":"MACEDONIA",

"Mesopotamiae":"MESOPOTAMIA",
"Mesopotamia":"MESOPOTAMIA",

"Osrhoenae":"OSRHOENE",
"Osroehenae":"OSRHOENE",
"Osrhoena":"OSRHOENE",

"Paflagoniae":"PAPHLAGONIA",

"Palaestinae":"PALAESTINA",
"Palaestina":"PALAESTINA",

"Pisidiae":"PISIDIA",
"Pisidia":"PISIDIA",

"Praeualitanae":"PRAEVALITANA",

"Raetiae":"RAETIA",

"Rhodopae":"RHODOPE",
"Rhodopa":"RHODOPE",

"Saradiniae":"SARDINIA",

"Scythiae":"SCYTHIA",
"Scythia":"SCYTHIA",

"Siciliae":"SICILIA",
"Sicilia":"SICILIA",

"Thebaidos":"THEBAIS",
"Thebais":"THEBAIS",

"Thessaliae":"THESSALIA",

"Thraciae":"THRACIA",
"Thracia":"THRACIA",

"Tripolitanae":"TRIPOLITANA",

"Tusciae et Umbriae":"TUSCIA ET UMBRIA",

"Valeriae":"VALERIA",

"Venetiae et Histriae":"VENETIA ET HISTRIA",

"Viennensis":"VIENNENSIS",

"Alpium Poeninarum et Graiarum":"ALPES GRAIAE ET POENINAE",

"Alpium maritimarum":"ALPES MARITIMAE",

"Aquitanicae primae":"AQUITANIA I",

"Aquitanicae secundae":"AQUITANIA II",

"Belgicae primae":"BELGICA I",

"Belgicae secundae":"BELGICA II",

"Byzacii":"BYZACENA",

"Germaniae primae":"GERMANIA I",

"Germaniae secundae":"GERMANIA II",

"Insularum":"INSULAE",

"Lugdunensis primae":"LUGDUNENSIS I",

"Lugdunensis secundae":"LUGDUNENSIS II",

"Narbonensis primae":"NARBONENSIS I",

"Narbonensis secundae":"NARBONENSIS II",

"Novempopulanae":"NOVEM POPULI",

"Ponti Polemoniaci":"PONTUS POLEMONIACUS",
"Pontus Polemoniacus":"PONTUS POLEMONIACUS",

"Saviae":"SAVIA",

"Maximae Sequanorum":"SEQUANIA"

}

geo = {}

with open(GEOJSON, encoding="utf-8") as f:

    gj = json.load(f)

for feature in gj["features"]:

    props = feature["properties"]

    name = props["PROV_NAME"].replace("\n", " ").strip()

    geo[name] = {
        "gisProvince": name,
        "canonicalName": name,
        "geojsonId":
            props.get("ID")
            or props.get("OBJECTID")
            or props.get("FID")
            or ""
    }

rows = []
seen = set()

print("INPUT Province :", NOTITIA)

with open(NOTITIA, encoding="utf-8") as f:

    for row in csv.DictReader(f):

        notitia = row["provinceName"].strip()

        if "Hellespont" in notitia:
            print(
        "DEBUG:",
        repr(notitia),
        "in MATCH =", notitia in MATCH,
        "canonical =", MATCH.get(notitia)
    )

        if notitia not in MATCH:
            continue

        canonical = MATCH[notitia]

        if canonical not in geo:
            print(
                "Missing GIS province:",
                canonical
            )
            continue

        key = (
            canonical,
            notitia
        )

        if key in seen:
            continue

        seen.add(key)

        rows.append({
            "gisProvince":
                geo[canonical]["gisProvince"],
            "canonicalName":
                canonical,
            "geojsonId":
                geo[canonical]["geojsonId"],
            "notitiaMatch":
                notitia,
            "status":
                "MATCH"
        })

with open(
    OUTPUT,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "gisProvince",
            "canonicalName",
            "geojsonId",
            "notitiaMatch",
            "status"
        ]
    )

    writer.writeheader()

    for row in sorted(
        rows,
        key=lambda r:(
            r["canonicalName"],
            r["notitiaMatch"]
        )
    ):
        writer.writerow(row)

print()
print("Living Notitia")
print("match_provinces.py")
print()
print("GIS provinces :", len(geo))
print("Matched       :", len(rows))
print("Output        :", OUTPUT)
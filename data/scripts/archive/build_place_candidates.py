#
# Living Notitia V3
# build_place_candidates.py
#
from pathlib import Path
import csv
import re
from collections import Counter
ROOT=Path(__file__).resolve().parents[3]
INPUT=ROOT/"csv"/"Place.csv"
OUTPUT=ROOT/"csv"/"PlaceCandidate.csv"
FIELDS=[
"candidateId",
"placeName",
"candidate",
"candidateNo",
"candidateType",
"chapter",
"document",
"nodeType",
"office",
"unit",
"canonicalName",
"province",
"region",
"latitude",
"longitude",
"confidence",
"notes"
]
PROVINCE_WORDS={
"Africae","Arabiae","Asiae","Baeticae","Belgicae",
"Bithyniae","Britanniae","Campaniae","Cariae",
"Corsicae","Cretae","Cypri","Daciae","Dalmatiae",
"Epiri","Europae","Galatiae","Galliarum",
"Liguriae","Lusitaniae","Macedoniae",
"Mesopotamiae","Moesiae","Narbonensis",
"Norici","Palaestinae","Pannoniae",
"Phoenices","Pisidiae","Ponti",
"Raetiae","Rhodopae","Scythiae",
"Siciliae","Syriae","Thebaidos",
"Thraciae","Tripolitanae",
"Tusciae","Valeriae","Viennensis"
}
REGION_WORDS={
"Galliarum",
"Italiae",
"Illyrici",
"Illyricum",
"Orientis",
"Africae"
}
COMMENT_PATTERN=re.compile(r"\[|\]|\?")
DOT_PATTERN=re.compile(r"^\.+$")
DESCRIPTION_WORDS={
"a",
"ab",
"ad",
"ali",
"alio",
"apud",
"circa",
"contra",
"et",
"ex",
"in",
"infra",
"inter",
"intra",
"iuxta",
"nunc",
"nune",
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
SPLITTERS=[
" siue ",
" sive ",
" - ",
" et ",
" contra "
]
IGNORE_PREFIXES=(
"aut ",
"ceteros ",
"consultationes ",
"et ",
"ali ",
"alio ",
"apud ",
"iuxta ",
"nunc ",
"nune "
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
def clean_candidate(text):
    text=re.sub(r"^\(.*?\)\s*","",text)
    text=re.sub(r"^\.+\s*","",text)
    text=" ".join(text.split())
    text=text.strip(" .,;:-()")
    return text
def split_candidates(name):
    text=clean_candidate(name)
    candidates=[text]
    for splitter in SPLITTERS:
        nextCandidates=[]
        for candidate in candidates:
            parts=candidate.split(splitter)
            for part in parts:
                part=clean_candidate(part)
                if part:
                    nextCandidates.append(part)
        candidates=nextCandidates
    result=[]
    seen=set()
    for candidate in candidates:
        candidate=clean_candidate(candidate)
        if not candidate:
            continue
        key=candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(candidate)
    return result
def classify_place(placeName):
    strippedName=placeName.strip()
    classificationName=re.sub(
        r"^[\s\.\,\;\:\-\(\)]+",
        "",
        strippedName
    ).strip()
    lowerName=classificationName.lower()
    paddedLower=f" {lowerName} "
    if COMMENT_PATTERN.search(strippedName):
        return "Comment"
    if DOT_PATTERN.fullmatch(strippedName):
        return "Noise"
    if not classificationName:
        return "Noise"
    if classificationName in REGION_WORDS:
        return "Region"
    if classificationName in PROVINCE_WORDS:
        return "Province"
    if lowerName.startswith(IGNORE_PREFIXES):
        return "Description"
    if any(text in paddedLower for text in IGNORE_CONTAINS):
        return "Description"
    words=classificationName.split()
    if len(words)>1 and words[0].lower() in DESCRIPTION_WORDS:
        return "Description"
    return "Place"
rows=[]
counter=Counter()
number=1
with open(INPUT,newline="",encoding="utf-8") as f:
    reader=csv.DictReader(f)
    for row in reader:
        placeName=row.get("placeName","").strip()
        if not placeName:
            continue
        candidateType=classify_place(placeName)
        if candidateType in {
            "Comment",
            "Description",
            "Noise"
        }:
            counter[candidateType]+=1
            continue
        candidateList=split_candidates(placeName)
        if not candidateList:
            counter["Noise"]+=1
            continue
        candidateNo=1
        for candidate in candidateList:
            rows.append({
                "candidateId":f"PLCAND{number:05d}",
                "placeName":placeName,
                "candidate":candidate,
                "candidateNo":candidateNo,
                "candidateType":candidateType,
                "chapter":row.get("chapter","").strip(),
                "document":row.get("document","").strip(),
                "nodeType":row.get("nodeType","").strip(),
                "office":row.get("office","").strip(),
                "unit":row.get("unit","").strip(),
                "canonicalName":"",
                "province":"",
                "region":"",
                "latitude":"",
                "longitude":"",
                "confidence":"",
                "notes":""
            })
            counter[candidateType]+=1
            number+=1
            candidateNo+=1
rows.sort(
    key=lambda r:(
        r["candidateType"],
        r["candidate"].lower(),
        r["placeName"].lower(),
        int(r["candidateNo"])
    )
)
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
with open(OUTPUT,"w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
print()
print("Living Notitia V3")
print("build_place_candidates.py")
print()
print("Candidates")
print("--------------------------------")
for key in sorted(counter):
    print(f"{key:15}{counter[key]:6}")
print()
print("Rows :",len(rows))
print("Output :",OUTPUT)
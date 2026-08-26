#!/usr/bin/env python3
from pathlib import Path
import csv
from collections import Counter,defaultdict
HERE=Path(__file__).resolve()
ROOT=None
for parent in [HERE.parent,*HERE.parents]:
    candidate=parent/"csv"/"PlaceAmbiguous_context.csv"
    if candidate.exists():
        ROOT=parent
        break
if ROOT is None:
    raise FileNotFoundError("Hittar inte csv/PlaceAmbiguous_context.csv i någon överordnad projektmapp")
CSV=ROOT/"csv"/"PlaceAmbiguous_context.csv"
with CSV.open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))
occ=defaultdict(list)
for r in rows:
    occ[r["occurrenceId"]].append(r)
def yes(v):
    return bool((v or "").strip())
def num(v):
    try:
        return float(v)
    except:
        return 0.0
def category(cands):
    statuses={r.get("contextStatus","") for r in cands}
    coords=sum(1 for r in cands if yes(r.get("latitude")) and yes(r.get("longitude")))
    exact=sum(1 for r in cands if num(r.get("nameSimilarity") or r.get("similarity"))>=0.999)
    if any(s in {"HARD_MATCH","HARD_NEAR_MATCH"} for s in statuses):
        return "MULTIPLE_HARD_MATCH"
    if any(s in {"SOFT_MATCH","SOFT_NEAR_MATCH"} for s in statuses):
        return "MULTIPLE_SOFT_MATCH"
    if exact>=2:
        return "MULTIPLE_EXACT_NAMES"
    if coords==0:
        return "NO_COORDINATES"
    if coords==1:
        return "ONE_COORDINATED_CANDIDATE"
    return "MULTIPLE_COORDINATED_CANDIDATES"
cats=Counter()
chapters=Counter()
candidate_counts=Counter()
for oid,cands in occ.items():
    cats[category(cands)]+=1
    chapters[cands[0].get("chapter","")]+=1
    candidate_counts[len(cands)]+=1
print("Living Notitia V3")
print("analyse_place_ambiguities_v2.py")
print("Project root          :",ROOT)
print("Ambiguous file        :",CSV)
print()
print("Ambiguous occurrences :",len(occ))
print("Candidate rows         :",len(rows))
print()
print("Ambiguity type:")
for k,n in cats.most_common():
    print(f"{n:4}  {k}")
print()
print("Number of candidates:")
for k,n in sorted(candidate_counts.items()):
    print(f"{n:4} occurrence(s) with {k} candidate(s)")
print()
print("Top chapters:")
for k,n in chapters.most_common(20):
    print(f"{n:4}  {k}")
print()
print("Potential easy wins:")
shown=0
for oid,cands in occ.items():
    cat=category(cands)
    if cat in {"ONE_COORDINATED_CANDIDATE","MULTIPLE_HARD_MATCH","MULTIPLE_SOFT_MATCH"}:
        r=cands[0]
        print(f"{oid} | {r.get('placeName','')} | {r.get('chapter','')} | {cat}")
        for c in cands[:5]:
            print(f"    {c.get('pleiadesId','')} {c.get('pleiadesName','')} | GIS {c.get('gisProvince','')} | {c.get('contextStatus','')} | sim {c.get('nameSimilarity',c.get('similarity',''))}")
        shown+=1
        if shown>=30:
            break
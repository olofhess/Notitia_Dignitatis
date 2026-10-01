#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
XML_FILE = BASE_DIR / "data" / "notitia.xml"
GAZETTEER_FILE = BASE_DIR / "csv" / "PlaceGazetteer.csv"
OUTPUT_FILE = BASE_DIR / "data" / "english_render.json"

def clean(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())

def norm(text):
    text = clean(text).lower()
    return re.sub(r"[.,;:]+$", "", text)

def load_gazetteer(path):
    index = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            for field in ("sourcePlaceName", "placeName", "pleiadesName"):
                key = norm(row.get(field))
                if key:
                    index.setdefault(key, []).append(row)
    return index

def choose_gazetteer_match(source_place, gazetteer):
    candidates = gazetteer.get(norm(source_place), [])
    if not candidates:
        return None
    exact = [r for r in candidates if norm(r.get("sourcePlaceName")) == norm(source_place)]
    if exact:
        candidates = exact
    confirmed = [r for r in candidates if norm(r.get("confidence")) == "confirmed"]
    if confirmed:
        candidates = confirmed
    return candidates[0]

FACTORY_TERMS = {
    "sagittaria": "arrow",
    "scutaria": "shield",
    "loricaria": "armour",
    "arcuaria": "bow",
    "spatharia": "sword",
    "hastaria": "spear",
    "armorum": "arms",
    "armamentaria": "arms",
    "balistaria": "ballista",
    "clibanaria": "heavy cavalry armour",
}

def strip_place_prefix(unit_text, source_place):
    unit = clean(unit_text).rstrip(".")
    place = clean(source_place).rstrip(".")
    if not place:
        return unit
    return clean(re.sub(rf"^{re.escape(place)}\b[\s,]*", "", unit, flags=re.IGNORECASE))

def split_latin_list(text):
    text = clean(text).rstrip(".")
    if not text:
        return []
    return [clean(p) for p in re.split(r"\s*,\s*|\s+et\s+", text, flags=re.IGNORECASE) if clean(p)]

def factory_phrase(descriptor):
    descriptor = clean(descriptor).rstrip(".")
    key = norm(descriptor)

    if not key:
        return "factory", []

    if key == "armorum omnium":
        return "factory for all kinds of arms", []

    if key == "scutorum, scordiscorum et armorum":
        return "factory for shields, saddles and arms", []

    translated = []
    unresolved = []

    for part in split_latin_list(descriptor):
        pkey = norm(part)
        if pkey == "scutorum":
            translated.append("shields")
        elif pkey == "scordiscorum":
            translated.append("saddles")
        elif pkey in FACTORY_TERMS:
            translated.append(FACTORY_TERMS[pkey])
        else:
            translated.append(part)
            unresolved.append(part)

    if len(translated) == 1:
        return f"{translated[0]} factory", unresolved
    if len(translated) == 2:
        return f"{translated[0]} and {translated[1]} factory", unresolved

    return f"{', '.join(translated[:-1])} and {translated[-1]} factory", unresolved

def child_text(element, tag):
    child = element.find(tag)
    return clean(child.text if child is not None else "")

def preferred_place_name(latin_place, row):
    if not row:
        return clean(latin_place)

    place_name = clean(row.get("placeName"))
    pleiades_name = clean(row.get("pleiadesName"))

    if (
        place_name
        and norm(place_name) == norm(latin_place)
        and pleiades_name
        and norm(pleiades_name) != norm(latin_place)
    ):
        return pleiades_name

    return place_name or pleiades_name or clean(latin_place)

def iter_factory_groups(root):
    for document in root.findall("document"):
        document_id = clean(document.get("id"))
        for chapter in document.findall("chapter"):
            chapter_title = child_text(chapter, "title")
            for group in chapter.iter("group"):
                if group.get("type") == "factoryGroup":
                    yield document_id, chapter_title, child_text(group, "title"), group

def render_factory(document_id, chapter_title, group_title, region_group, factory, gazetteer):
    line = clean(factory.get("line"))
    latin_unit = child_text(factory, "unit")
    latin_place = child_text(factory, "place")
    latin_province = child_text(factory, "province")
    region_title = child_text(region_group, "title")

    row = choose_gazetteer_match(latin_place, gazetteer)
    place_name = preferred_place_name(latin_place, row)

    descriptor = strip_place_prefix(latin_unit, latin_place)
    phrase, unresolved = factory_phrase(descriptor)

    english = phrase[0].upper() + phrase[1:]
    if place_name:
        english += f" at {place_name}"

    status = "ok"
    notes = []

    if not row:
        status = "review"
        notes.append("No exact PlaceGazetteer match for the Latin place.")

    if unresolved:
        status = "review"
        notes.append("Unresolved terminology: " + ", ".join(unresolved))

    if not descriptor:
        if status == "ok":
            status = "inferred_from_context"
        notes.append("Factory type is not stated; 'Factory' supplied from Fabricae context.")

    if "..." in latin_unit:
        if status == "ok":
            status = "inferred_from_context"
        english = f"Factory at {place_name}" if place_name else "Factory"
        notes.append("Editorial ellipsis ignored; production type is not stated.")

    result = {
        "line": int(line) if line.isdigit() else line,
        "document": document_id,
        "chapter": chapter_title,
        "group": group_title,
        "region": region_title,
        "entryType": "factory",
        "latin": latin_unit,
        "latinPlace": latin_place,
        "province": latin_province or None,
        "english": english,
        "status": status,
    }

    if row:
        result["place"] = {
            "gazetteerId": clean(row.get("gazetteerId")) or None,
            "name": place_name,
            "sourcePlaceName": clean(row.get("sourcePlaceName")) or None,
            "pleiadesId": clean(row.get("pleiadesId")) or None,
            "pleiadesName": clean(row.get("pleiadesName")) or None,
            "latitude": clean(row.get("latitude")) or None,
            "longitude": clean(row.get("longitude")) or None,
            "confidence": clean(row.get("confidence")) or None,
        }
    else:
        result["place"] = {"name": place_name or None}

    if notes:
        result["notes"] = notes

    return result


TREASURY_PROVINCES = {
    "dalmatiae": "Dalmatia",
    "saviae": "Savia",
    "pannoniae primae": "Pannonia Prima",
    "venetiae": "Venetia",
    "liguriae": "Liguria",
    "raetiae secundae": "Raetia Secunda",
}

def english_province(latin_province):
    key = norm(latin_province)
    if not key:
        return ""
    return TREASURY_PROVINCES.get(key, clean(latin_province))

def iter_treasury_groups(root):
    for document in root.findall("document"):
        document_id = clean(document.get("id"))
        for chapter in document.findall("chapter"):
            chapter_title = child_text(chapter, "title")
            for group in chapter.iter("group"):
                title = child_text(group, "title")
                if norm(title).startswith("praepositi thesaur"):
                    yield document_id, chapter_title, title, group

def render_treasury(document_id, chapter_title, group_title,
                    region_group, entry, gazetteer):
    line = clean(entry.get("line"))
    office = child_text(entry, "office")
    latin_unit = child_text(entry, "unit")
    latin_place = child_text(entry, "place")
    latin_province = child_text(entry, "province")
    region_title = child_text(region_group, "title")

    row = choose_gazetteer_match(latin_place, gazetteer)

    # Britain is deliberately conservative. "Augustensium" tells us that
    # an Augusta-name is involved, but this renderer must not decide which
    # British Augusta without a context-aware geographic match.
    british_augusta = (
        norm(region_title) == "in britanniis"
        and norm(latin_place) == "augustensium"
    )

    if british_augusta:
        place_name = "Augusta"
        row = None
    elif norm(latin_place) == "romae":
        place_name = "Rome"
    else:
        place_name = preferred_place_name(latin_place, row)

    english = "Superintendent of the treasury"
    if place_name:
        english += f" at {place_name}"

    province_name = english_province(latin_province)
    if province_name:
        english += f", in {province_name}"

    status = "ok"
    notes = []

    if british_augusta:
        status = "review"
        notes.append(
            "British 'Augustensium' is not geographically resolved; "
            "the renderer preserves only the place-name base 'Augusta'."
        )
    elif not row and norm(latin_place) != "romae":
        status = "review"
        notes.append("No exact PlaceGazetteer match for the Latin place.")

    result = {
        "line": int(line) if line.isdigit() else line,
        "document": document_id,
        "chapter": chapter_title,
        "group": group_title,
        "region": region_title,
        "entryType": "treasury",
        "office": office or "Praepositus",
        "latin": clean(" ".join(x for x in (office, latin_unit) if x)),
        "latinPlace": latin_place,
        "province": latin_province or None,
        "english": english,
        "status": status,
    }

    if row:
        result["place"] = {
            "gazetteerId": clean(row.get("gazetteerId")) or None,
            "name": place_name,
            "sourcePlaceName": clean(row.get("sourcePlaceName")) or None,
            "pleiadesId": clean(row.get("pleiadesId")) or None,
            "pleiadesName": clean(row.get("pleiadesName")) or None,
            "latitude": clean(row.get("latitude")) or None,
            "longitude": clean(row.get("longitude")) or None,
            "confidence": clean(row.get("confidence")) or None,
        }
    else:
        result["place"] = {"name": place_name or None}

    if notes:
        result["notes"] = notes

    return result

def main():
    missing = [p for p in (XML_FILE, GAZETTEER_FILE) if not p.exists()]
    if missing:
        print("Missing required file(s):", file=sys.stderr)
        for p in missing:
            print(f"  {p}", file=sys.stderr)
        return 1

    root = ET.parse(XML_FILE).getroot()
    gazetteer = load_gazetteer(GAZETTEER_FILE)
    entries = {}

    for document_id, chapter_title, group_title, factory_group in iter_factory_groups(root):
        for region_group in factory_group.findall("group"):
            for factory in region_group.findall("factory"):
                rendered = render_factory(
                    document_id, chapter_title, group_title,
                    region_group, factory, gazetteer
                )
                entries[f"{document_id}:{rendered['line']}"] = rendered

    for document_id, chapter_title, group_title, treasury_group in iter_treasury_groups(root):
        for region_group in treasury_group.findall("group"):
            for entry in list(region_group):
                if entry.tag == "title":
                    continue
                if child_text(entry, "unit").lower().startswith("thesaurorum"):
                    rendered = render_treasury(
                        document_id, chapter_title, group_title,
                        region_group, entry, gazetteer
                    )
                    entries[f"{document_id}:{rendered['line']}"] = rendered

    output = {
        "source": XML_FILE.name,
        "gazetteer": GAZETTEER_FILE.name,
        "scope": ["Fabricae", "Praepositi thesaurorum"],
        "entryCount": len(entries),
        "entries": entries,
    }

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")

    ok_count = sum(e["status"] == "ok" for e in entries.values())
    inferred_count = sum(e["status"] == "inferred_from_context" for e in entries.values())
    review_count = sum(e["status"] == "review" for e in entries.values())
    factory_count = sum(e["entryType"] == "factory" for e in entries.values())
    treasury_count = sum(e["entryType"] == "treasury" for e in entries.values())

    print(f"Wrote: {OUTPUT_FILE}")
    print(f"Fabricae entries: {factory_count}")
    print(f"Treasury entries: {treasury_count}")
    print(f"Total entries: {len(entries)}")
    print(f"OK: {ok_count}")
    print(f"Inferred from context: {inferred_count}")
    print(f"Review: {review_count}")

if __name__ == "__main__":
    raise SystemExit(main())

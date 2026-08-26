#!/usr/bin/env python3
from pathlib import Path
import re
import shutil
from datetime import datetime
from collections import Counter
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve()
ROOT=next((p for p in HERE.parents if (p/"data"/"Notitia_OCC.txt").exists() and (p/"data"/"Notitia_oriens.txt").exists()),None)
if ROOT is None:
    raise FileNotFoundError("Kan inte hitta projektroten med data/Notitia_OCC.txt och data/Notitia_oriens.txt")
INPUTS=[
    ("Occidentis",ROOT/"data"/"Notitia_OCC.txt"),
    ("Oriens",ROOT/"data"/"Notitia_oriens.txt")
]
OUTPUT=ROOT/"data"/"notitia.xml"
ROMAN=re.compile(r"^([IVXLCDM]+)\.\s*(.*)$")
CHAPTER_DICTIONARY=[
    ("Comes domesticorum","comes_domesticorum"),
    ("Comes limitis","comes_limitis"),
    ("Comes litoris","comes_litoris"),
    ("Comes ","comes"),
    ("Dux ","dux"),
    ("Primicerius","primicerius"),
    ("Insignia","insignia"),
    ("Sub dispositione","prefecture")
]
HEADING_DICTIONARY=[
    ("Sub dispositione","administration"),
    ("Officium","officium"),
    ("In provincia","province"),
    ("Intra","region"),
    ("Per ","region"),
    ("In ","region")
]
UNIT_DICTIONARY=[
    ("Legio","legion"),
    ("legionis","legion"),
    ("Cohors","cohort"),
    ("cohortis","cohort"),
    ("Ala","ala"),
    ("alae","ala"),
    ("Equites","equites"),
    ("equitum","equites"),
    ("Cuneus","cuneus"),
    ("Milites","milites"),
    ("militum","milites"),
    ("Auxilia","auxilia"),
    ("Auxilium","auxilia"),
    ("classis","fleet"),
    ("numeri","numerus"),
    ("Rationalis","civil"),
    ("Procurator","civil"),
    ("Curator","civil"),
    ("Tractus","tractus")
]
OFFICE_DICTIONARY=[
    ("Praefectus","praefectus"),
    ("Praepositus","praepositus"),
    ("Tribunus","tribunus"),
    ("Procurator","procurator"),
    ("Rationalis","rationalis"),
    ("Curator","curator"),
    ("Comes","comes"),
    ("Dux","dux"),
    ("Vicarius","vicarius")
]
REGION_FORMS={
    "africa","africae","britannia","britanniae","britanniarum","britannis","gallia","galliae","galliarum","hispania","hispaniae","hispaniarum","illyricum","illyrici","italia","italiae","oriens","orientis","asiana","asianae","pontica","ponticae","thraciae","thraciarum"
}
PROVINCE_FORMS={
    "achaia","achaiae","aegyptus","aegypti","aemilia","aemiliae","apulia","apuliae","apuliae et calabriae","arabia","arabiae","armenia","armeniae","asia","asiae","baetica","baeticae","belgica prima","belgica secunda","belgicae primae","belgicae secundae","bithynia","bithyniae","byzacii","byzacium","calabria","calabriae","campania","campaniae","cappadocia","cappadociae","caria","cariae","cilicia","ciliciae","corsica","corsicae","creta","cretae","cypri","dacia mediterranea","dacia ripensis","daciae mediterraneae","daciae ripensis","dalmatia","dalmatiae","dardania","dardaniae","epirus nova","epirus noua","epirus vetus","epirus uetus","epiri novae","epiri nouae","epiri veteris","epiri ueteris","flaminiae","foenice","foenicis","gallaeciae","germania prima","germania secunda","germaniae primae","germaniae secundae","hellesponti","isauria","isauriae","liguria","liguriae","lucania","lucaniae","lyciae et pamphyliae","lydia","lydiae","macedonia","macedoniae","mauretania caesariensis","mauretania sitifensis","mauretaniae caesariensis","mauretaniae sitifensis","mesopotamia","mesopotamiae","moesia prima","moesia secunda","moesiae primae","moesiae secundae","narbonensis primae","narbonensis secundae","norici mediterranei","norici ripensis","numidia","numidiae","osrhoena","osrhoenae","palaestina","palaestinae","pannonia prima","pannonia secunda","pannoniae primae","pannoniae secundae","phrygiae","pisidiae","praevalitana","praevalitanae","raetia prima","raetia secunda","raetiae primae","raetiae secundae","sardinia","sardiniae","savia","saviae","scythia","scythiae","sicilia","siciliae","syria","syriae","thebais","thebaidos","thessalia","thessaliae","thracia","thraciae","tingitaniae","tripolis","tripolitana","tripolitanae","tusciae","valeria","valeriae","venetia","venetiae","venetiae et histriae","venetiae inferioris","viennensis"
}
PLACE_BEARING_PREFIXES=("thesaurorum","gynaeciorum","gynaecii","gynaecei","linyfii","bafii","monetae","argentariorum")
PRODUCTION_WORDS=("armorum","armamentaria","sagittaria","loricaria","scutaria","scutorum","arcuaria","spatharia","balistaria","clibanaria","hastaria")
NON_GEO_TAIL_WORDS=set(PRODUCTION_WORDS)|{"officium","officiales","milites","equites","cohors","cohortis","ala","alae","legio","legionis"}
STATION_PREFIXES=("legionis","cohortis","alae","classis","numeri","militum","equitum","cuneus","equites","milites","auxilia","auxilium","ala","cohors","legio","sarmatarum","laetorum")
STATS=Counter()
def clean(text):
    text=(text or "").strip()
    if text.endswith(".") and "," not in text and ":" not in text and ";" not in text:
        text=text[:-1]
    return text
def folded(text):
    return re.sub(r"\s+"," ",clean(text).casefold())
def strip_editorial_notes(text):
    value=re.sub(r"\[[^\]]*\]","",text or "")
    return re.sub(r"\s+"," ",value).strip()
def classify(text,dictionary):
    for pattern,value in dictionary:
        if text.startswith(pattern):
            return value
    return "unknown"
def indent(element,level=0):
    space="\n"+"    "*level
    if len(element):
        if not element.text or not element.text.strip():
            element.text=space+"    "
        for child in element:
            indent(child,level+1)
        if not child.tail or not child.tail.strip():
            child.tail=space
    elif level:
        if not element.tail or not element.tail.strip():
            element.tail=space
def parseChapter(document,titleText):
    chapterType=classify(titleText,CHAPTER_DICTIONARY)
    chapter=ET.SubElement(document,"chapter",type=chapterType)
    ET.SubElement(chapter,"title").text=titleText
    return chapter
def parseHeading(parent,text,lineNumber):
    headingType=classify(text,HEADING_DICTIONARY)
    group=ET.SubElement(parent,"group",type=headingType,line=str(lineNumber))
    ET.SubElement(group,"title").text=clean(text[:-1])
    return group
def strip_admin_prefix(text):
    value=clean(text)
    value=re.sub(r"^(?:provinciae?|in\s+provincia)\s+","",value,flags=re.I)
    return clean(value)
def geo_tail_value(text):
    value=strip_admin_prefix(text)
    key=folded(value)
    if key.startswith("in ") and key[3:] in REGION_FORMS:
        return clean(value[3:])
    return value
def classify_geo_tail(text):
    value=geo_tail_value(text)
    key=folded(value)
    key=re.sub(r"\s*-\s*translat[ai]\s+.*$","",key)
    if key in REGION_FORMS:
        return "region"
    if key in PROVINCE_FORMS:
        return "province"
    if any(word in key.split() for word in NON_GEO_TAIL_WORDS):
        return "none"
    return "place"
def append_geo(node,tag,text,source):
    value=clean(text)
    if not value:
        return
    attrs={"source":source} if source else {}
    ET.SubElement(node,tag,attrs).text=value
    STATS[tag]+=1
def split_place_phrase(phrase):
    phrase=clean(phrase)
    phrase=re.sub(r"^(?:urbis|civitatis)\s+","",phrase,flags=re.I)
    parts=[clean(x) for x in re.split(r"\s+et\s+",phrase,flags=re.I)]
    return [x for x in parts if x]
def trim_embedded_phrase(phrase):
    value=clean(phrase)
    value=re.sub(r"^\([^)]*\)\s*","",value)
    value=re.split(r"\s+-\s+|\s+rei\s+privatae\b|\s+translat[ai]\b",value,maxsplit=1,flags=re.I)[0]
    low=folded(value)
    for province in sorted(PROVINCE_FORMS,key=len,reverse=True):
        if low.endswith(" "+province):
            value=value[:-(len(province))].strip(" ,")
            break
    return clean(value)
def embedded_place_refs(unit,officeType):
    value=clean(unit)
    low=folded(value)
    refs=[]
    def add_phrase(phrase,source):
        phrase=trim_embedded_phrase(phrase)
        for ref in split_place_phrase(phrase):
            refs.append((ref,source))
    if officeType in {"praepositus","procurator","rationalis","curator"}:
        for prefix in PLACE_BEARING_PREFIXES:
            marker=prefix+" "
            pos=low.find(marker)
            if pos>=0:
                phrase=value[pos+len(marker):]
                add_phrase(phrase,"unit")
                break
    m=re.search(r"\blimitis\s+(.+?)(?=\s+in\s+castris\b|$)",value,flags=re.I)
    if m:
        add_phrase(m.group(1),"limes")
    for m in re.finditer(r"\bin\s+castris\s+(.+?)(?=\s+-\s+|$)",value,flags=re.I):
        add_phrase(m.group(1),"castris")
    out=[]
    seen=set()
    for ref,source in refs:
        key=folded(ref)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append((ref,source))
    return out
def append_embedded_admin_geo(node,unit,officeType):
    if officeType not in {"praepositus","procurator","rationalis","curator"}:
        return
    value=clean(unit)
    low=folded(value)
    phrase=""
    for prefix in PLACE_BEARING_PREFIXES:
        marker=prefix+" "
        pos=low.find(marker)
        if pos>=0:
            phrase=value[pos+len(marker):]
            break
    if not phrase:
        return
    m=re.match(r"^\(in\s+([^)]+)\)\s+",phrase,flags=re.I)
    if m:
        region=clean(m.group(1))
        if folded(region) in REGION_FORMS:
            append_geo(node,"region",region,"unit")
    main=re.split(r"\s+-\s+|\s+translat[ai]\b|\s+rei\s+privatae\b",phrase,maxsplit=1,flags=re.I)[0]
    lowmain=folded(main)
    for province in sorted(PROVINCE_FORMS,key=len,reverse=True):
        if lowmain.endswith(" "+province):
            append_geo(node,"province",province,"unit")
            break
    m=re.search(r"\s+-\s+(.+)$",phrase)
    if m:
        target=clean(m.group(1))
        if target:
            append_geo(node,"place",target,"transfer")
def append_admin_geo(node,text,source="tail"):
    value=clean(text)
    raw_key=folded(value)
    stripped=strip_admin_prefix(value)
    key=folded(stripped)
    if raw_key.startswith("regionis "):
        append_geo(node,"region",value,source)
        return True
    if raw_key.startswith("per tractum ") or raw_key.startswith("inter ") or raw_key.startswith("iuxta "):
        append_geo(node,"region",value,source)
        return True
    if raw_key.startswith("a ") and raw_key.endswith(" usque"):
        append_geo(node,"region",value,source)
        return True
    if key in REGION_FORMS:
        append_geo(node,"region",stripped,source)
        return True
    if key in PROVINCE_FORMS:
        append_geo(node,"province",stripped,source)
        return True
    return False
def split_tail_geography(node,text,source="tail"):
    value=clean(text)
    if not value:
        return True
    if append_admin_geo(node,value,source):
        return True
    m=re.match(r"^\(in\s+([^)]+)\)\s+(.+)$",value,flags=re.I)
    if m:
        context=clean(m.group(1))
        place=clean(m.group(2))
        if folded(context) in PROVINCE_FORMS:
            append_geo(node,"province",context,"tail")
            append_geo(node,"place",place,source)
            STATS["embedded_place"]+=1
            STATS["source_"+source]+=1
            return True
        if folded(context) in REGION_FORMS:
            append_geo(node,"region",context,"tail")
            append_geo(node,"place",place,source)
            STATS["embedded_place"]+=1
            STATS["source_"+source]+=1
            return True
    m=re.match(r"^(.+?)\s+in\s+(.+)$",value,flags=re.I)
    if m:
        place=clean(m.group(1))
        context=clean(m.group(2))
        if folded(context) in PROVINCE_FORMS:
            append_geo(node,"place",place,source)
            STATS["embedded_place"]+=1
            STATS["source_"+source]+=1
            append_geo(node,"province",context,"tail")
            return True
        if folded(context) in REGION_FORMS:
            append_geo(node,"place",place,source)
            STATS["embedded_place"]+=1
            STATS["source_"+source]+=1
            append_geo(node,"region",context,"tail")
            return True
    low=folded(value)
    for candidate in sorted(PROVINCE_FORMS,key=len,reverse=True):
        if low.endswith(" "+candidate):
            place_text=value[:-len(candidate)].strip(" ,")
            if place_text:
                append_geo(node,"place",place_text,source)
                STATS["embedded_place"]+=1
                STATS["source_"+source]+=1
            append_geo(node,"province",candidate,"tail")
            return True
    for candidate in sorted(REGION_FORMS,key=len,reverse=True):
        if low.endswith(" "+candidate):
            place_text=value[:-len(candidate)].strip(" ,")
            if place_text:
                append_geo(node,"place",place_text,source)
                STATS["embedded_place"]+=1
                STATS["source_"+source]+=1
            append_geo(node,"region",candidate,"tail")
            return True
    return False
def is_station_bearing(unit,officeType):
    low=folded(unit)
    if any(low.startswith(prefix+" ") or low==prefix for prefix in STATION_PREFIXES):
        return True
    if officeType in {"praefectus","tribunus","praepositus"}:
        return any(re.search(r"\b"+re.escape(prefix)+r"\b",low) for prefix in STATION_PREFIXES)
    return False
def parse_station_tail(node,text,source="tail"):
    value=clean(text)
    if not value:
        return
    m=re.match(r"^(.+?),\s*nun[ce]\s+(.+)$",value,flags=re.I)
    if m:
        parse_station_tail(node,m.group(1),source)
        second=clean(m.group(2))
        low_second=folded(second)
        if low_second.startswith("in burgo contra ") or low_second.startswith("in castello contra ") or low_second.startswith("contra "):
            append_geo(node,"region",second,"alternate")
        else:
            parse_station_tail(node,second,"alternate")
        return
    if append_admin_geo(node,value,source):
        return
    m=re.match(r"^prope\s+(.+)$",value,flags=re.I)
    if m:
        inner=clean(m.group(1))
        if not split_tail_geography(node,inner,"prope"):
            append_geo(node,"place",inner,"prope")
            STATS["embedded_place"]+=1
            STATS["source_prope"]+=1
        return
    m=re.match(r"^in\s+castris\s+(.+)$",value,flags=re.I)
    if m:
        inner=clean(m.group(1))
        append_geo(node,"place",inner,"castris")
        STATS["embedded_place"]+=1
        STATS["source_castris"]+=1
        return
    m=re.match(r"^in\s+loco\s+(.+)$",value,flags=re.I)
    if m:
        value=clean(m.group(1))
    m=re.match(r"^contra\s+(.+?)\s+in\s+barbarico\s+in\s+castello\s+(.+)$",value,flags=re.I)
    if m:
        append_geo(node,"place",clean(m.group(2)),"castello")
        STATS["embedded_place"]+=1
        STATS["source_castello"]+=1
        return
    if folded(value).startswith("in castello contra ") or folded(value).startswith("contra "):
        append_geo(node,"region",value,source)
        return
    if split_tail_geography(node,value,source):
        return
    parts=[clean(x) for x in re.split(r"\s+siue\s+",value,flags=re.I)]
    parts=[x for x in parts if x]
    if len(parts)>1:
        for part in parts:
            append_geo(node,"place",part,source)
            STATS["embedded_place"]+=1
            STATS["source_"+source]+=1
        return
    append_geo(node,"place",value,source)
def parse_transfer_note(node,text):
    m=re.search(r"\btranslat[ai]\s+(.+)$",text,flags=re.I)
    if not m:
        return
    target=clean(m.group(1))
    if target and folded(target)!="anhelat":
        append_geo(node,"place",target,"transfer")
def starts_production(text):
    value=folded(text).lstrip(";")
    return any(re.match(r"^"+re.escape(word)+r"\b",value,flags=re.I) for word in PRODUCTION_WORDS)
def factory_place_prefix(text):
    value=clean(text).lstrip(";")
    prod_re=r"^(.+?)\s+(?:"+"|".join(re.escape(word) for word in PRODUCTION_WORDS)+r")\b"
    m=re.match(prod_re,value,flags=re.I)
    if not m:
        return ""
    return re.sub(r"\.+$","",clean(m.group(1)))
def parseFactoryFields(node,text):
    value=clean(text).rstrip(":").strip()
    value=value.lstrip(";").strip()
    if "," in value:
        left,right=value.split(",",1)
        left=clean(left)
        right=clean(right)
        if starts_production(left):
            ET.SubElement(node,"unit").text=left
            if not split_tail_geography(node,right):
                tag=classify_geo_tail(right)
                if tag!="none":
                    append_geo(node,tag,geo_tail_value(right),"tail")
                else:
                    STATS["ignored_tail"]+=1
            STATS["factory_entry"]+=1
            return node
        prefix=factory_place_prefix(left)
        ET.SubElement(node,"unit").text=value
        if prefix:
            append_geo(node,"place",prefix,"factory")
            STATS["embedded_place"]+=1
            STATS["source_factory"]+=1
        else:
            candidate=re.sub(r"\.+$","",left).strip()
            if candidate:
                append_geo(node,"place",candidate,"factory")
                STATS["embedded_place"]+=1
                STATS["source_factory"]+=1
        STATS["factory_entry"]+=1
        return node
    if starts_production(value):
        first,_,rest=value.partition(" ")
        rest=clean(rest)
        if rest and not folded(rest).startswith("et "):
            ET.SubElement(node,"unit").text=first
            if not split_tail_geography(node,rest):
                tag=classify_geo_tail(rest)
                if tag!="none":
                    append_geo(node,tag,geo_tail_value(rest),"factory")
            STATS["factory_entry"]+=1
            return node
        ET.SubElement(node,"unit").text=value
        STATS["factory_entry"]+=1
        return node
    prefix=factory_place_prefix(value)
    ET.SubElement(node,"unit").text=value
    candidate=prefix or re.sub(r"\.+$","",value).strip()
    if candidate:
        append_geo(node,"place",candidate,"factory")
        STATS["embedded_place"]+=1
        STATS["source_factory"]+=1
    STATS["factory_entry"]+=1
    return node
def parseFields(node,text,suppressTailGeo=False):
    original=clean(text)
    text=clean(strip_editorial_notes(original))
    office=""
    officeType="unknown"
    tail=""
    left=text
    if "," in text and not suppressTailGeo:
        left,right=text.split(",",1)
        left=clean(left)
        tail=clean(right)
    elif "," in text and suppressTailGeo:
        STATS["officium_tail_suppressed"]+=1
    words=left.split()
    if words:
        officeType=classify(words[0],OFFICE_DICTIONARY)
        if officeType!="unknown":
            office=words[0]
            words=words[1:]
    unit=" ".join(words)
    if office:
        ET.SubElement(node,"office",type=officeType).text=office
    ET.SubElement(node,"unit").text=unit
    for ref,source in embedded_place_refs(unit,officeType):
        append_geo(node,"place",ref,source)
        STATS["embedded_place"]+=1
        STATS["source_"+source]+=1
    if not tail:
        append_embedded_admin_geo(node,unit,officeType)
    if tail:
        if append_admin_geo(node,tail,"tail"):
            pass
        elif is_station_bearing(unit,officeType):
            parse_station_tail(node,tail,"tail")
        else:
            STATS["non_station_tail_suppressed"]+=1
        parse_transfer_note(node,tail)
    else:
        parse_transfer_note(node,unit)
    return node
def parseTypedNode(parent,nodeType,text,lineNumber,suppressTailGeo=False,factoryMode=False):
    node=ET.SubElement(parent,nodeType,line=str(lineNumber))
    if factoryMode:
        return parseFactoryFields(node,text)
    return parseFields(node,text,suppressTailGeo=suppressTailGeo)
def dispatchUnit(parent,text,lineNumber,suppressTailGeo=False,factoryMode=False):
    nodeType=classify(text,UNIT_DICTIONARY)
    return parseTypedNode(parent,nodeType,text,lineNumber,suppressTailGeo=suppressTailGeo,factoryMode=factoryMode)
def stack_has_officium(stack):
    return any(group.get("type")=="officium" for group in stack)
def parseDocument(name,path):
    document=ET.Element("document",id=name)
    chapter=None
    stack=[]
    factoryMode=False
    with path.open(encoding="utf-8-sig") as file:
        for lineNumber,line in enumerate(file,1):
            raw=line.rstrip()
            if not raw:
                continue
            text=raw.strip()
            m=ROMAN.match(text)
            if m:
                chapter=parseChapter(document,clean(m.group(2)))
                stack=[]
                factoryMode=False
                continue
            if chapter is None:
                ET.SubElement(document,"text",line=str(lineNumber)).text=clean(text)
                continue
            level=(len(raw)-len(raw.lstrip()))//5
            while len(stack)>level:
                stack.pop()
            parent=stack[-1] if stack else chapter
            if text.endswith(":"):
                if folded(text).startswith("fabricae "):
                    factoryMode=True
                elif folded(text).startswith("officium"):
                    factoryMode=False
                if factoryMode and starts_production(text.rstrip(":")):
                    dispatchUnit(parent,text,lineNumber,factoryMode=True)
                    continue
                group=parseHeading(parent,text,lineNumber)
                stack.append(group)
                continue
            dispatchUnit(parent,text,lineNumber,suppressTailGeo=stack_has_officium(stack),factoryMode=factoryMode)
    return document
def backup_output():
    if not OUTPUT.exists():
        return None
    archive=OUTPUT.parent/"archive"
    archive.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
    target=archive/f"notitia_{stamp}.xml"
    shutil.copy2(OUTPUT,target)
    return target
def build():
    STATS.clear()
    root=ET.Element("notitia")
    for name,path in INPUTS:
        root.append(parseDocument(name,path))
    indent(root)
    backup=backup_output()
    ET.ElementTree(root).write(OUTPUT,encoding="utf-8",xml_declaration=True)
    print()
    print("Living Notitia V4")
    print("build_notitia_xml_v4.py")
    print()
    print("Documents                :",len(INPUTS))
    print("Place elements           :",STATS["place"])
    print("  derived geography      :",STATS["embedded_place"])
    print("    ordinary unit        :",STATS["source_unit"])
    print("    factory context      :",STATS["source_factory"])
    print("    limes                :",STATS["source_limes"])
    print("    in castris           :",STATS["source_castris"])
    print("    prope                :",STATS["source_prope"])
    print("Factory entries          :",STATS["factory_entry"])
    print("Province elements        :",STATS["province"])
    print("Region elements          :",STATS["region"])
    print("Ignored non-geo tails    :",STATS["ignored_tail"])
    print("Officium tails suppressed:",STATS["officium_tail_suppressed"])
    print("Non-station tails suppressed:",STATS["non_station_tail_suppressed"])
    print()
    print("Output :",OUTPUT)
    if backup:
        print("Backup :",backup)
if __name__=="__main__":
    build()
#!/usr/bin/env python3
from pathlib import Path
import csv
import re
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve()
ROOT=next((p for p in HERE.parents if (p/'data'/'Notitia_OCC.txt').exists() and (p/'data'/'Notitia_oriens.txt').exists()),None)
if ROOT is None:
    raise FileNotFoundError('Kan inte hitta projektroten med data/Notitia_OCC.txt och data/Notitia_oriens.txt')
XML_PATH=ROOT/'data'/'notitia.xml'
OUT_DIR=ROOT/'data'/'work'
PLACE_OUT=OUT_DIR/'PlaceMention.csv'
AUDIT_OUT=OUT_DIR/'PlaceMention_Audit.txt'
SOURCE_FILES={'Occidentis':ROOT/'data'/'Notitia_OCC.txt','Oriens':ROOT/'data'/'Notitia_oriens.txt'}
ADMIN_WORDS={'provincia','provinciae','dioecesis','dioeceses','officium','officii','regio','regionis','tractus'}
def clean(text):
    return re.sub(r'\s+',' ',(text or '').strip())
def folded(text):
    return clean(text).casefold()
def load_source_lines(path):
    with path.open(encoding='utf-8-sig') as f:
        return ['']+[line.rstrip('\n\r') for line in f]
def direct_text(node,tag):
    child=node.find(tag)
    return clean(child.text) if child is not None else ''
def chapter_title(node):
    title=node.find('title')
    return clean(title.text) if title is not None else ''
def group_title(node):
    title=node.find('title')
    return clean(title.text) if title is not None else ''
def row_source_text(lines,line_number):
    if not line_number or line_number<1 or line_number>=len(lines):
        return ''
    return clean(lines[line_number])
def walk(node,document,lines,chapter='',groups=(),inside_officium=False,rows=None,issues=None):
    if rows is None:
        rows=[]
    if issues is None:
        issues=[]
    current_chapter=chapter
    current_groups=groups
    current_officium=inside_officium
    if node.tag=='chapter':
        current_chapter=chapter_title(node)
        current_groups=()
        current_officium=False
    elif node.tag=='group':
        title=group_title(node)
        current_groups=groups+(title,)
        current_officium=inside_officium or node.get('type')=='officium' or folded(title).startswith('officium')
    line_text=node.get('line') or ''
    line_number=int(line_text) if line_text.isdigit() else 0
    direct_places=[child for child in list(node) if child.tag=='place']
    if direct_places:
        source_text=row_source_text(lines,line_number)
        office=node.find('office')
        office_text=clean(office.text) if office is not None else ''
        office_type=office.get('type','') if office is not None else ''
        unit_text=direct_text(node,'unit')
        for place in direct_places:
            literal=clean(place.text)
            source=place.get('source','')
            rows.append({'document':document,'line':line_number,'literalForm':literal,'source':source,'nodeType':node.tag,'officeType':office_type,'office':office_text,'unit':unit_text,'chapter':current_chapter,'groupPath':' / '.join(current_groups),'sourceText':source_text,'pointEligible':'1','issue':''})
            key=folded(literal)
            row=rows[-1]
            if current_officium:
                row['pointEligible']='0'
                row['issue']='PLACE_INSIDE_OFFICIUM'
                issues.append((document,line_number,'PLACE_INSIDE_OFFICIUM',literal,source_text))
            if not literal:
                row['pointEligible']='0'
                row['issue']='EMPTY_PLACE'
                issues.append((document,line_number,'EMPTY_PLACE','',source_text))
            if literal and source_text and folded(literal) not in folded(source_text):
                row['pointEligible']='0'
                row['issue']='LITERAL_NOT_IN_SOURCE'
                issues.append((document,line_number,'LITERAL_NOT_IN_SOURCE',literal,source_text))
            words=set(re.findall(r"[a-z]+",key))
            if words & ADMIN_WORDS:
                row['pointEligible']='0'
                row['issue']='ADMIN_WORD_IN_PLACE'
                issues.append((document,line_number,'ADMIN_WORD_IN_PLACE',literal,source_text))
    for child in list(node):
        if child.tag in {'title','office','unit','place','province','region'}:
            continue
        walk(child,document,lines,current_chapter,current_groups,current_officium,rows,issues)
    return rows,issues
def main():
    if not XML_PATH.exists():
        raise FileNotFoundError(f'Saknar {XML_PATH}')
    sources={name:load_source_lines(path) for name,path in SOURCE_FILES.items()}
    root=ET.parse(XML_PATH).getroot()
    rows=[]
    issues=[]
    for document in root.findall('document'):
        name=document.get('id','')
        lines=sources.get(name,[''])
        walk(document,name,lines,rows=rows,issues=issues)
    rows.sort(key=lambda r:(r['document'],r['line'],folded(r['literalForm']),r['source']))
    for index,row in enumerate(rows,1):
        row['mentionId']=f'PM{index:06d}'
    seen=set()
    deduped=[]
    for row in rows:
        key=(row['document'],row['line'],folded(row['literalForm']),row['source'])
        if key in seen:
            issues.append((row['document'],row['line'],'DUPLICATE_MENTION',row['literalForm'],row['sourceText']))
            continue
        seen.add(key)
        deduped.append(row)
    rows=deduped
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    fields=['mentionId','document','line','literalForm','source','pointEligible','issue','nodeType','officeType','office','unit','chapter','groupPath','sourceText']
    with PLACE_OUT.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    by_source={}
    by_document={}
    by_line={}
    for row in rows:
        by_source[row['source']]=by_source.get(row['source'],0)+1
        by_document[row['document']]=by_document.get(row['document'],0)+1
        key=(row['document'],row['line'])
        by_line[key]=by_line.get(key,0)+1
    multi_lines=[(key,count) for key,count in by_line.items() if count>1]
    unique_literals=len({folded(row['literalForm']) for row in rows})
    eligible=sum(row['pointEligible']=='1' for row in rows)
    review=len(rows)-eligible
    with AUDIT_OUT.open('w',encoding='utf-8') as f:
        f.write('Living Notitia - PlaceMention audit\n')
        f.write('===================================\n')
        f.write(f'XML: {XML_PATH}\n')
        f.write(f'Place mentions: {len(rows)}\n')
        f.write(f'Unique literal forms: {unique_literals}\n')
        f.write(f'Point-eligible mentions: {eligible}\n')
        f.write(f'Mentions requiring review: {review}\n')
        f.write(f'Source lines with >1 place mention: {len(multi_lines)}\n')
        f.write(f'Potential integrity issues: {len(issues)}\n')
        f.write('\nBy document\n')
        for key in sorted(by_document):
            f.write(f'  {key}: {by_document[key]}\n')
        f.write('\nBy extraction source\n')
        for key in sorted(by_source,key=lambda x:(x=='',x)):
            label=key or '(none)'
            f.write(f'  {label}: {by_source[key]}\n')
        f.write('\nIntegrity issues\n')
        if not issues:
            f.write('  none\n')
        else:
            for document,line,kind,literal,source_text in sorted(issues,key=lambda x:(x[0],x[1],x[2],x[3])):
                f.write(f'  {document} line {line}: {kind}: {literal}\n')
                if source_text:
                    f.write(f'    {source_text}\n')
        f.write('\nRule for publication\n')
        f.write('  Only rows with pointEligible=1 may create point locations.\n')
        f.write('  Rows with pointEligible=0 remain in the audit table but must not be published as points.\n')
        f.write('  Province, region, diocese, tractus and other administrative areas are not point locations.\n')
    print()
    print('Living Notitia')
    print('audit_place_mentions.py')
    print()
    print('Place mentions          :',len(rows))
    print('Unique literal forms    :',unique_literals)
    print('Point-eligible mentions :',eligible)
    print('Mentions for review     :',review)
    print('Integrity issues        :',len(issues))
    print('PlaceMention.csv        :',PLACE_OUT)
    print('Audit report            :',AUDIT_OUT)
if __name__=='__main__':
    main()
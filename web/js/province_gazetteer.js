//
// Living Notitia
// province_gazetteer.js
//
// Central resolver between Notitia province forms
// and provinces.geojson OBJECTID values.
//

const FILE = "../csv/ProvinceGazetteer.csv";

let rows = [];
let byProvinceId = new Map();
let byNotitiaForm = new Map();
let bySourceRef = new Map();

function normalize(value){
    return String(value || "")
        .normalize("NFKC")
        .trim()
        .replace(/[.?:;,]+$/,"")
        .replace(/\s+/g," ")
        .toLowerCase();
}

function splitPipe(value){
    return String(value || "")
        .split("|")
        .map(item=>item.trim())
        .filter(Boolean);
}

function parseCSV(text){

    const result=[];
    let row=[];
    let field="";
    let quoted=false;

    for(let i=0;i<text.length;i++){

        const ch=text[i];

        if(ch === '"'){
            if(quoted && text[i+1] === '"'){
                field+='"';
                i++;
            }
            else{
                quoted=!quoted;
            }
            continue;
        }

        if(ch === "," && !quoted){
            row.push(field);
            field="";
            continue;
        }

        if((ch === "\n" || ch === "\r") && !quoted){

            if(ch === "\r" && text[i+1] === "\n"){
                i++;
            }

            row.push(field);
            field="";

            if(row.some(value=>value !== "")){
                result.push(row);
            }

            row=[];
            continue;
        }

        field+=ch;
    }

    row.push(field);

    if(row.some(value=>value !== "")){
        result.push(row);
    }

    if(!result.length){
        return [];
    }

    const headers=result[0].map(value=>value.trim());

    return result.slice(1).map(values=>{

        const record={};

        headers.forEach((header,index)=>{
            record[header]=(values[index] ?? "").trim();
        });

        return record;
    });
}

function prepare(record){

    const prepared={
        ...record,
        notitiaForms:splitPipe(record.notitiaForms),
        sourceRefs:splitPipe(record.sourceRefs),
        geoObjectIds:splitPipe(record.geoObjectIds)
            .map(Number)
            .filter(Number.isFinite),
        geojsonNames:splitPipe(record.geojsonNames),
        geojsonDioceses:splitPipe(record.geojsonDioceses)
    };

    return prepared;
}

function indexRows(){

    byProvinceId=new Map();
    byNotitiaForm=new Map();
    bySourceRef=new Map();

    for(const row of rows){

        byProvinceId.set(
            row.provinceId,
            row
        );

        for(const sourceRef of row.sourceRefs){
            bySourceRef.set(
                normalize(sourceRef),
                row
            );
        }

        const forms=new Set([
            row.canonicalName,
            ...row.notitiaForms
        ]);

        for(const form of forms){

            const key=normalize(form);

            if(!key){
                continue;
            }

            const existing=
                byNotitiaForm.get(key) || [];

            if(!existing.includes(row)){
                existing.push(row);
            }

            byNotitiaForm.set(
                key,
                existing
            );
        }
    }
}

export async function initialize(){

    const response=await fetch(
        FILE,
        { cache:"no-store" }
    );

    if(!response.ok){
        throw new Error(
            `Could not load ${FILE}: HTTP ${response.status}`
        );
    }

    const text=await response.text();

    rows=parseCSV(text)
        .map(prepare);

    indexRows();

    return rows.length;
}

export function resolve(value,document=null){

    const matches=
        byNotitiaForm.get(
            normalize(value)
        ) || [];

    if(!document){
        return matches;
    }

    const wanted=
        normalize(document);

    return matches.filter(row=>
        normalize(row.document)===wanted
    );
}

export function resolveOne(value,document=null){

    const matches=
        resolve(
            value,
            document
        );

    return matches.length===1
        ? matches[0]
        : null;
}

export function geoObjectIds(value,document=null){

    const ids=
        resolve(
            value,
            document
        )
        .flatMap(row=>row.geoObjectIds);

    return [...new Set(ids)];
}

export function resolveSource(document,line){

    const sourceRef=
        normalize(
            `${document || ""}:${line || ""}`
        );

    return bySourceRef.get(sourceRef) || null;
}

export function geoObjectIdsForSource(document,line){

    const row=resolveSource(
        document,
        line
    );

    return row
        ? [...row.geoObjectIds]
        : [];
}

export function geojsonNames(value,document=null){

    const names=
        resolve(
            value,
            document
        )
        .flatMap(row=>row.geojsonNames);

    return [...new Set(names)];
}

export function byId(provinceId){
    return byProvinceId.get(provinceId) || null;
}

export function all(){
    return [...rows];
}

export function count(){
    return rows.length;
}

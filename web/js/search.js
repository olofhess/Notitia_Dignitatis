//
// Living Notitia
// search.js
// Step 8: bilingual ranked search with explicit two-term AND / OR
//

import * as XML from "./xml.js";

let searchIndex=[];
let englishDocument=null;
let englishLoadPromise=null;

export function initialize(){
    buildIndex();
    englishLoadPromise=loadEnglish()
        .then(()=>{
            buildIndex();
            console.log("BILINGUAL SEARCH INDEX",searchIndex.length,"records");
            runConsoleTests();
            return searchIndex;
        })
        .catch(error=>{
            console.warn("English search index unavailable; Latin search remains active.",error);
            return searchIndex;
        });
    return englishLoadPromise;
}

export function ready(){
    return englishLoadPromise||Promise.resolve(searchIndex);
}

export function records(){
    return searchIndex;
}

export function search(queryOrOptions=""){
    const query=normalize(
        typeof queryOrOptions==="string"
            ? queryOrOptions
            : queryOrOptions?.text||""
    );

    if(!query){
        return [];
    }

    const booleanQuery=parseBooleanQuery(query);

    if(booleanQuery){
        const { left, operator, right }=booleanQuery;

        if(operator==="or"){
            return searchOr(left,right);
        }

        return searchAnd([left,right]);
    }

    //
    // Existing behaviour is preserved:
    // a plain multi-word query is still an implicit AND search.
    //
    const terms=query.split(" ").filter(Boolean);

    if(terms.length===1){
        return searchSingleTerm(terms[0]);
    }

    return searchAnd(terms);
}
function parseBooleanQuery(query){
    const match=query.match(/^(.+?)\s+(and|or)\s+(.+)$/i);

    if(!match){
        return null;
    }

    const left=normalize(match[1]);
    const operator=normalize(match[2]);
    const right=normalize(match[3]);

    if(!left||!right){
        return null;
    }

    //
    // Deliberately support one Boolean operator only.
    // No parentheses, NOT, or chained Boolean expressions.
    //
    if(/\s+(and|or)\s+/i.test(left)||/\s+(and|or)\s+/i.test(right)){
        return null;
    }

    return { left, operator, right };
}

function searchAnd(terms){
    return searchIndex
        .map(record=>rankRecordTerms(record,terms))
        .filter(Boolean)
        .sort((a,b)=>{
            if(b.score!==a.score){
                return b.score-a.score;
            }
            return lineNumber(a.line)-lineNumber(b.line);
        });
}

function searchSingleTerm(term){
    const ranked=searchIndex
        .map(record=>rankRecordTerms(record,[term]))
        .filter(Boolean)
        .sort((a,b)=>{
            if(b.score!==a.score){
                return b.score-a.score;
            }
            return lineNumber(a.line)-lineNumber(b.line);
        });

    const strong=ranked.filter(record=>
        record.matchType==="exact" ||
        record.matchType==="whole"
    );

    return strong.length
        ? strong
        : ranked;
}

function searchOr(left,right){
    const combined=new Map();

    for(const term of [left,right]){
        for(const record of searchSingleTerm(term)){
            const key=record.node;

            if(!combined.has(key)){
                combined.set(key,{
                    ...record,
                    booleanOperator:"or",
                    booleanTerms:[term],
                    matchedBooleanTerms:1
                });
                continue;
            }

            const existing=combined.get(key);
            const terms=[...new Set([...existing.booleanTerms,term])];

            if(record.score>existing.score){
                combined.set(key,{
                    ...record,
                    booleanOperator:"or",
                    booleanTerms:terms,
                    matchedBooleanTerms:terms.length
                });
            }
            else{
                existing.booleanTerms=terms;
                existing.matchedBooleanTerms=terms.length;
            }
        }
    }

    return [...combined.values()]
        .sort((a,b)=>{
            if(b.matchedBooleanTerms!==a.matchedBooleanTerms){
                return b.matchedBooleanTerms-a.matchedBooleanTerms;
            }
            if(b.score!==a.score){
                return b.score-a.score;
            }
            return lineNumber(a.line)-lineNumber(b.line);
        });
}

// Temporary compatibility with the old search_ui.js.
// These can disappear when the new search UI is built.
export function placeSources(){
    return uniqueSorted(
        searchIndex
            .flatMap(record=>record.places.map(place=>place.source))
            .filter(Boolean)
    );
}

export function officeTypes(){
    return uniqueSorted(
        searchIndex
            .map(record=>record.officeType)
            .filter(Boolean)
    );
}

export function ownerOffices(){
    return uniqueSorted(
        searchIndex
            .map(record=>record.ownerOffice)
            .filter(Boolean)
    );
}

export function dimensions(){
    return uniqueSorted(
        searchIndex
            .filter(record=>record.unit)
            .map(record=>record.dimension)
            .filter(Boolean)
    );
}

function buildIndex(){
    searchIndex=[];
    XML.documents().forEach(document=>walk(document));
    console.log(
        englishDocument ? "SEARCH INDEX LATIN + ENGLISH" : "SEARCH INDEX LATIN",
        searchIndex.length,
        "records"
    );
}

function walk(node){
    searchIndex.push(createRecord(node));
    navigationChildren(node).forEach(child=>walk(child));
}

function navigationChildren(node){
    if(XML.attr(node,"line") && node.tagName!=="group"){
        return [];
    }
    return XML.children(node);
}

function createRecord(node){
    const englishNode=parallelEnglishNode(node);
    const documentNode=ancestorOrSelf(node,"document");
    const chapterNode=ancestorOrSelf(node,"chapter");
    const officiumNode=ancestorOfficium(node);
    const officeNode=directChild(node,"office");
    const unitNode=directChild(node,"unit");
    const englishOfficeNode=directChild(englishNode,"office");
    const englishUnitNode=directChild(englishNode,"unit");
    const places=directChildren(node,"place").map(place=>({
        name:clean(place.textContent),
        source:clean(place.getAttribute("source"))
    }));
    const latinTitle=directTitle(node);
    const englishTitle=directTitle(englishNode);
    const latinOffice=clean(officeNode?.textContent);
    const englishOffice=clean(englishOfficeNode?.textContent);
    const latinUnit=clean(unitNode?.textContent);
    const englishUnit=clean(englishUnitNode?.textContent);
    const latinText=primaryText(node);
    const englishText=primaryText(englishNode);
    const latinContext=contextTitles(node);
    const englishContext=contextTitles(englishNode);
    const document=clean(documentNode?.getAttribute("id"));
    const chapter=directTitle(chapterNode);
    const englishChapter=directTitle(parallelEnglishNode(chapterNode));
    const ownerOffice=clean(officiumNode?.getAttribute("ownerOffice"));
    const officeType=clean(officeNode?.getAttribute("type"));
    const dimension=node.tagName;
    const latinSearchText=normalize([
        latinText,
        latinTitle,
        latinOffice,
        officeType,
        latinUnit,
        ownerOffice,
        ...places.map(place=>place.name),
        ...places.map(place=>place.source),
        chapter,
        ...latinContext,
        document
    ].filter(Boolean).join(" "));
    const englishSearchText=normalize([
        englishText,
        englishTitle,
        englishOffice,
        englishUnit,
        englishChapter,
        ...englishContext,
        ...places.map(place=>place.name),
        document
    ].filter(Boolean).join(" "));
    const searchText=normalize(latinSearchText+" "+englishSearchText);
    return {
        node,
        englishNode,
        line:clean(node.getAttribute("line")),
        dimension,
        document,
        chapter,
        englishChapter,
        officeType,
        ownerOffice,
        places,
        latinText,
        englishText,
        latinTitle,
        englishTitle,
        latinOffice,
        englishOffice,
        office:latinOffice,
        latinUnit,
        englishUnit,
        unit:latinUnit,
        latinContext,
        englishContext,
        context:latinContext,
        latinSearchText,
        englishSearchText,
        searchText
    };
}

async function loadEnglish(){
    const response=await fetch("../data/notitia.en.xml");
    if(!response.ok){
        throw new Error("Could not load ../data/notitia.en.xml: "+response.status);
    }
    const text=await response.text();
    const parser=new DOMParser();
    const document=parser.parseFromString(text,"application/xml");
    const parserError=document.querySelector("parsererror");
    if(parserError){
        throw new Error("notitia.en.xml is not valid XML");
    }
    englishDocument=document;
}

function parallelEnglishNode(node){
    if(!node || !englishDocument){
        return null;
    }
    const sourceDocument=ancestorOrSelf(node,"document");
    if(!sourceDocument){
        return null;
    }
    const documentId=clean(sourceDocument.getAttribute("id"));
    const englishRoot=Array.from(
        englishDocument.getElementsByTagName("document")
    ).find(candidate=>clean(candidate.getAttribute("id"))===documentId);
    if(!englishRoot){
        return null;
    }
    if(node===sourceDocument){
        return englishRoot;
    }
    const path=elementPath(sourceDocument,node);
    let current=englishRoot;
    for(const index of path){
        const children=Array.from(current.children);
        current=children[index]||null;
        if(!current){
            break;
        }
    }
    if(current && current.tagName===node.tagName){
        return current;
    }
    const line=clean(node.getAttribute("line"));
    if(line){
        return Array.from(englishRoot.querySelectorAll("[line]")).find(
            candidate=>clean(candidate.getAttribute("line"))===line
        )||null;
    }
    return null;
}

function elementPath(root,node){
    const path=[];
    let current=node;
    while(current && current!==root){
        const parent=current.parentElement;
        if(!parent){
            return [];
        }
        path.unshift(Array.from(parent.children).indexOf(current));
        current=parent;
    }
    return current===root ? path : [];
}

function primaryText(node){
    if(!node){
        return "";
    }

    const title=directTitle(node);

    if(title){
        return title;
    }

    //
    // Never fall back to node.textContent here.
    // For container nodes that would pull in the complete descendant tree
    // and make a chapter/document match words that occur only far below it.
    //
    // Search only direct semantic children that represent this node itself.
    //
    const searchableTags=new Set([
        "office",
        "unit",
        "place",
        "province",
        "region",
        "function",
        "factory",
        "treasury"
    ]);

    const parts=Array.from(node.children)
        .filter(child=>searchableTags.has(child.tagName))
        .map(child=>clean(child.textContent))
        .filter(Boolean);

    if(parts.length){
        return clean(parts.join(" "));
    }

    //
    // Leaf nodes with no element children may legitimately carry their
    // own text directly.
    //
    if(node.children.length===0){
        return clean(node.textContent);
    }

    return "";
}


function rankRecordTerms(record,terms){
    const termMatches=[];

    for(const term of terms){
        const ranked=rankRecord(record,term);

        if(!ranked){
            return null;
        }

        termMatches.push({
            term,
            score:ranked.score,
            matchType:ranked.matchType,
            primaryMatch:ranked.primaryMatch,
            matches:ranked.matches
        });
    }

    //
    // Step 7 ranking for multi-word queries:
    //
    // 1. Prefer records where more search terms match a DIRECT field
    //    of the record itself (office, unit, title, place, text).
    //
    // 2. Then let the weakest individual term decide. This prevents
    //    one excellent hit from hiding the fact that another term is
    //    only a distant contextual match.
    //
    // 3. Finally use the sum of all term scores as a tie-breaker.
    //
    const directTermCount=termMatches.filter(match=>
        match.matches.some(fieldMatch=>fieldMatch.scope==="direct")
    ).length;

    const weakestScore=Math.min(...termMatches.map(match=>match.score));
    const totalScore=termMatches.reduce((sum,match)=>sum+match.score,0);

    const score=
        directTermCount*1000000000 +
        weakestScore*1000 +
        totalScore;

    const allMatches=termMatches.flatMap(match=>
        match.matches.map(fieldMatch=>({
            term:match.term,
            ...fieldMatch
        }))
    );

    const best=allMatches
        .slice()
        .sort((a,b)=>b.score-a.score)[0];

    const languages=[...new Set(allMatches.flatMap(match=>
        match.language==="both" ? ["la","en"] : [match.language]
    ))];

    return {
        ...record,
        score,
        matchType:best?.type||"",
        primaryMatch:best||null,
        matches:allMatches,
        termMatches,
        directTermCount,
        matchLanguages:languages,
        matchFields:[...new Set(allMatches.map(match=>match.field))]
    };
}

function rankRecord(record,query){
    const candidates=[
        ["latinText",record.latinText,"la",140,"direct"],
        ["englishText",record.englishText,"en",140,"direct"],
        ["latinTitle",record.latinTitle,"la",130,"direct"],
        ["englishTitle",record.englishTitle,"en",130,"direct"],
        ["latinOffice",record.latinOffice,"la",120,"direct"],
        ["englishOffice",record.englishOffice,"en",120,"direct"],
        ["latinUnit",record.latinUnit,"la",120,"direct"],
        ["englishUnit",record.englishUnit,"en",120,"direct"],
        ["places",record.places.map(place=>place.name).join(" "),"both",110,"direct"],
        ["placeSources",record.places.map(place=>place.source).join(" "),"la",100,"direct"],
        ["chapter",record.chapter,"la",80,"context"],
        ["englishChapter",record.englishChapter,"en",80,"context"],
        ["latinContext",record.latinContext.join(" "),"la",50,"context"],
        ["englishContext",record.englishContext.join(" "),"en",50,"context"],
        ["officeType",record.officeType,"la",35,"context"],
        ["ownerOffice",record.ownerOffice,"la",35,"context"],
        ["document",record.document,"both",20,"context"]
    ];

    const matches=[];
    for(const [field,value,language,fieldWeight,scope] of candidates){
        const match=scoreValue(value,query,fieldWeight,scope);
        if(match){
            matches.push({
                field,
                language,
                scope,
                ...match
            });
        }
    }

    if(!matches.length){
        return null;
    }

    matches.sort((a,b)=>b.score-a.score);
    const best=matches[0];
    const languages=[...new Set(matches.flatMap(match=>
        match.language==="both" ? ["la","en"] : [match.language]
    ))];

    return {
        ...record,
        score:best.score,
        matchType:best.type,
        primaryMatch:best,
        matches,
        matchLanguages:languages,
        matchFields:[...new Set(matches.map(match=>match.field))]
    };
}

function scoreValue(value,query,fieldWeight,scope){
    const text=normalize(value);
    if(!text){
        return null;
    }

    const contextPenalty=scope==="context" ? 120 : 0;

    if(text===query){
        return {
            type:"exact",
            score:1000+fieldWeight-contextPenalty
        };
    }

    if(hasWholePhrase(text,query)){
        return {
            type:"whole",
            score:750+fieldWeight-contextPenalty
        };
    }

    if(hasWordPrefix(text,query)){
        return {
            type:"prefix",
            score:550+fieldWeight-contextPenalty
        };
    }

    if(text.includes(query)){
        return {
            type:"substring",
            score:350+fieldWeight-contextPenalty
        };
    }

    return null;
}

function hasWholePhrase(text,query){
    const pattern=new RegExp("(^|[^a-z0-9])"+escapeRegex(query)+"($|[^a-z0-9])","i");
    return pattern.test(text);
}

function hasWordPrefix(text,query){
    const pattern=new RegExp("(^|[^a-z0-9])"+escapeRegex(query),"i");
    return pattern.test(text);
}

function escapeRegex(value){
    return value.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");
}

function lineNumber(value){
    const number=Number.parseInt(value,10);
    return Number.isFinite(number) ? number : Number.MAX_SAFE_INTEGER;
}

function matchLanguages(record,query){
    const result=[];
    if(record.latinSearchText.includes(query)){
        result.push("la");
    }
    if(record.englishSearchText.includes(query)){
        result.push("en");
    }
    return result;
}

function matchFields(record,query){
    const fields=[];
    const candidates={
        latinText:record.latinText,
        englishText:record.englishText,
        latinTitle:record.latinTitle,
        englishTitle:record.englishTitle,
        latinOffice:record.latinOffice,
        englishOffice:record.englishOffice,
        latinUnit:record.latinUnit,
        englishUnit:record.englishUnit,
        latinContext:record.latinContext.join(" "),
        englishContext:record.englishContext.join(" "),
        places:record.places.map(place=>place.name).join(" ")
    };
    Object.entries(candidates).forEach(([name,value])=>{
        if(normalize(value).includes(query)){
            fields.push(name);
        }
    });
    return fields;
}

function runConsoleTests(){
    const tests=["scutaria","shield factory","equites","cavalry","bafii balearum","balearum bafii","procurator dalmatia","dalmatia procurator","procurator balearum"];
    tests.forEach(query=>{
        const results=search(query);
        console.log(
            "RANKED SEARCH TEST",
            JSON.stringify(query),
            results.length,
            "hits",
            results.slice(0,8).map(record=>({
                score:record.score,
                matchType:record.matchType,
                field:record.primaryMatch?.field,
                line:record.line,
                latin:record.latinText,
                english:record.englishText
            }))
        );
    });
}

function directChild(node,name){
    if(!node){
        return null;
    }
    return Array.from(node.children).find(child=>child.tagName===name)||null;
}

function directChildren(node,name){
    if(!node){
        return [];
    }
    return Array.from(node.children).filter(child=>child.tagName===name);
}

function directTitle(node){
    return clean(directChild(node,"title")?.textContent);
}

function ancestorOrSelf(node,name){
    let current=node;
    while(current){
        if(current.tagName===name){
            return current;
        }
        current=current.parentElement;
    }
    return null;
}

function ancestorOfficium(node){
    let current=node;
    while(current){
        if(current.tagName==="group" && current.getAttribute("type")==="officium"){
            return current;
        }
        if(current.tagName==="document"){
            break;
        }
        current=current.parentElement;
    }
    return null;
}

function contextTitles(node){
    if(!node){
        return [];
    }
    const result=[];
    let current=node.parentElement;
    while(current){
        if(current.tagName==="group"){
            const title=directTitle(current);
            if(title){
                result.unshift(title);
            }
        }
        if(current.tagName==="document"){
            break;
        }
        current=current.parentElement;
    }
    return result;
}

function uniqueSorted(values){
    return [...new Set(values)].sort((a,b)=>a.localeCompare(b,undefined,{sensitivity:"base"}));
}

function clean(value){
    return String(value||"").replace(/\s+/g," ").trim();
}

function normalize(value){
    return clean(value)
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g,"")
        .toLowerCase();
}
